"""Refresh the small mutable current-season game feed without rebuilding Pages."""
from __future__ import annotations

import json
import math
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public/data"
USER_AGENT = "Saturday-Lab/1.0 (+https://github.com/heimweh17/saturday-lab)"


def fetch_json(url, attempts=3):
    error = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.load(response)
        except Exception as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(attempt + 1)
    raise error


def numeric(value):
    if isinstance(value, dict):
        value = value.get("value", value.get("displayValue"))
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def pair(value, separator):
    try:
        left, right = str(value).split(separator, 1)
        return numeric(left), numeric(right)
    except ValueError:
        return None, None


def possession(value):
    try:
        minutes, seconds = str(value).split(":", 1)
        return float(minutes) + float(seconds) / 60
    except (TypeError, ValueError):
        return None


def normalized_box(statistics):
    values = {row.get("name"): row.get("displayValue") for row in statistics}
    completions, pass_attempts = pair(values.get("completionAttempts"), "/")
    third_made, third_attempts = pair(values.get("thirdDownEff"), "-")
    fourth_made, fourth_attempts = pair(values.get("fourthDownEff"), "-")
    penalties, penalty_yards = pair(values.get("totalPenaltiesYards"), "-")
    rush_attempts = numeric(values.get("rushingAttempts"))
    total_yards = numeric(values.get("totalYards"))
    plays = None if pass_attempts is None or rush_attempts is None else pass_attempts + rush_attempts
    return {
        "firstDowns": numeric(values.get("firstDowns")),
        "totalYards": total_yards,
        "passYards": numeric(values.get("netPassingYards")),
        "rushYards": numeric(values.get("rushingYards")),
        "passCompletions": completions,
        "passAttempts": pass_attempts,
        "rushAttempts": rush_attempts,
        "plays": plays,
        "yardsPerPlay": None if not plays or total_yards is None else total_yards / plays,
        "thirdMade": third_made,
        "thirdAttempts": third_attempts,
        "thirdRate": None if not third_attempts or third_made is None else third_made / third_attempts,
        "fourthMade": fourth_made,
        "fourthAttempts": fourth_attempts,
        "turnovers": numeric(values.get("turnovers")),
        "penalties": penalties,
        "penaltyYards": penalty_yards,
        "possessionMinutes": possession(values.get("possessionTime")),
    }


def schedule_game(event, fbs_ids):
    competition = event["competitions"][0]
    competitors = competition.get("competitors", [])
    if len(competitors) != 2:
        return None
    home = next(row for row in competitors if row["homeAway"] == "home")
    away = next(row for row in competitors if row["homeAway"] == "away")
    status = competition["status"]["type"]
    broadcasts = competition.get("broadcasts", [])
    names = [name for row in broadcasts for name in row.get("names", [])]
    return {
        "id": str(event["id"]),
        "season": int(event.get("season", {}).get("year", 0) or 0),
        "week": int(event.get("week", {}).get("number") or 0),
        "date": event["date"],
        "home": str(home["id"]),
        "away": str(away["id"]),
        "homeName": home["team"]["displayName"],
        "awayName": away["team"]["displayName"],
        "neutral": bool(competition.get("neutralSite", False)),
        "fbs": str(home["id"]) in fbs_ids and str(away["id"]) in fbs_ids,
        "status": status["name"],
        "state": status["state"],
        "statusDetail": status.get("detail") or status.get("description") or status["name"],
        "completed": bool(status.get("completed")),
        "timeValid": bool(competition.get("timeValid", False)),
        "hs": numeric(home.get("score")),
        "as": numeric(away.get("score")),
        "broadcast": ", ".join(dict.fromkeys(names)) or None,
        "source": f'https://www.espn.com/college-football/game/_/gameId/{event["id"]}',
    }


def game_detail(game):
    data = fetch_json(
        "https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary"
        f'?event={game["id"]}'
    )
    competition = data.get("header", {}).get("competitions", [{}])[0]
    competitors = competition.get("competitors", [])
    detail = {"periods": None, "box": None, "venue": None, "attendance": None}
    if len(competitors) == 2:
        home = next((row for row in competitors if row.get("homeAway") == "home"), None)
        away = next((row for row in competitors if row.get("homeAway") == "away"), None)
        if home and away:
            detail["periods"] = {
                "away": [int(float(row["displayValue"])) for row in away.get("linescores", [])],
                "home": [int(float(row["displayValue"])) for row in home.get("linescores", [])],
            }
    box_rows = data.get("boxscore", {}).get("teams", [])
    if game["state"] in ("in", "post") and box_rows:
        detail["box"] = {
            str(row["team"]["id"]): normalized_box(row.get("statistics", [])) for row in box_rows
        }
    info = data.get("gameInfo", {})
    venue = info.get("venue", {})
    if venue:
        address = venue.get("address", {})
        detail["venue"] = {
            "name": venue.get("fullName"),
            "city": address.get("city"),
            "state": address.get("state"),
        }
    detail["attendance"] = numeric(info.get("attendance"))
    header_broadcasts = competition.get("broadcasts", [])
    broadcast = ", ".join(
        dict.fromkeys(
            name
            for row in header_broadcasts
            for name in ([row.get("media", {}).get("shortName")] if row.get("media") else [])
            if name
        )
    )
    if broadcast:
        detail["broadcast"] = broadcast
    return detail


def canonical(payload):
    return json.dumps({k: v for k, v in payload.items() if k != "updatedAt"}, sort_keys=True, separators=(",", ":"))


def pregame_prediction(game, season_data):
    snapshot = season_data["snapshots"]["99"]
    teams = {team["id"]: team for team in snapshot["teams"]}
    home, away = teams.get(game["home"]), teams.get(game["away"])
    model = season_data.get("model")
    if not home or not away or not model or not home.get("modelState") or not away.get("modelState"):
        return None
    home_state, away_state = home["modelState"], away["modelState"]
    if not home_state.get("q") or not away_state.get("q"):
        return None

    def rest(state):
        if not state.get("lastDate"):
            return 7.0
        kickoff = datetime.fromisoformat(game["date"].replace("Z", "+00:00"))
        previous = datetime.fromisoformat(state["lastDate"].replace("Z", "+00:00"))
        return max(3.0, min(21.0, (kickoff - previous).total_seconds() / 86400))

    features = [
        *(a - b for a, b in zip(home_state["q"], away_state["q"])),
        0.0 if game["neutral"] else 1.0,
        rest(home_state) - rest(away_state),
    ]
    logit = sum(value * coefficient for value, coefficient in zip(features, model["coefficients"]))
    probability = 1 / (1 + math.exp(-max(-30, min(30, logit))))
    return {
        "homeWinProbability": probability,
        "modelVersion": model["version"],
        "snapshotThrough": snapshot.get("through"),
        "calculatedAt": datetime.now(timezone.utc).isoformat(),
    }


def main():
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    season = int(manifest["latestSeason"])
    season_data = json.loads((DATA / f"{season}.json").read_text(encoding="utf-8"))
    fbs_ids = {team["id"] for team in season_data["snapshots"]["99"]["teams"]}
    destination = DATA / f"live-{season}.json"
    old = json.loads(destination.read_text(encoding="utf-8")) if destination.exists() else None
    old_games = {game["id"]: game for game in old.get("games", [])} if old else {}
    archived_predictions = {row["id"]: row for row in season_data.get("predictions", [])}

    events = {}
    failures = []

    def fetch_team(team_id):
        return fetch_json(
            "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/"
            f"{team_id}/schedule?season={season}"
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {pool.submit(fetch_team, team_id): team_id for team_id in sorted(fbs_ids)}
        for future in as_completed(jobs):
            try:
                data = future.result()
            except Exception as exc:
                failures.append({"team": jobs[future], "error": str(exc)})
                continue
            for event in data.get("events", []):
                game = schedule_game(event, fbs_ids)
                if game:
                    existing = events.get(game["id"])
                    if existing and (existing["home"], existing["away"]) != (game["home"], game["away"]):
                        raise AssertionError(f'conflicting event identity {game["id"]}')
                    events[game["id"]] = game
    if failures:
        raise RuntimeError(f"schedule coverage failed for {len(failures)} teams: {failures[:3]}")

    now = datetime.now(timezone.utc)
    details_needed = []
    for game in events.values():
        prior = old_games.get(game["id"])
        if game["state"] == "pre":
            current_through = season_data["snapshots"]["99"].get("through")
            prior_pregame = (prior or {}).get("pregame") or {}
            if prior and prior.get("date") == game["date"] and prior_pregame.get("snapshotThrough") == current_through:
                game["pregame"] = prior["pregame"]
            else:
                game["pregame"] = pregame_prediction(game, season_data)
        elif prior and prior.get("pregame"):
            game["pregame"] = prior["pregame"]
            game["pregame"].setdefault("frozenAt", now.isoformat())
        elif game["id"] in archived_predictions:
            archived = archived_predictions[game["id"]]
            game["pregame"] = {
                "homeWinProbability": archived["prob"],
                "modelVersion": archived.get("modelVersion", model["version"] if (model := season_data.get("model")) else "archived"),
                "snapshotThrough": archived.get("cutoff"),
                "calculatedAt": archived.get("cutoff"),
                "frozenAt": archived.get("cutoff"),
            }
        changed = not prior or any(prior.get(key) != game.get(key) for key in ("status", "state", "hs", "as", "date"))
        kickoff = datetime.fromisoformat(game["date"].replace("Z", "+00:00"))
        near_kickoff = now - timedelta(days=2) <= kickoff <= now + timedelta(days=2)
        missing_detail = not prior or not prior.get("detail")
        if game["state"] == "in" or (game["completed"] and changed) or (near_kickoff and missing_detail):
            details_needed.append(game)
        elif prior and prior.get("detail"):
            game["detail"] = prior["detail"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {pool.submit(game_detail, game): game for game in details_needed}
        for future in as_completed(jobs):
            game = jobs[future]
            game["detail"] = future.result()

    payload = {
        "version": 1,
        "season": season,
        "updatedAt": now.isoformat(),
        "weeklySnapshotThrough": season_data["snapshots"]["99"].get("through"),
        "source": "Public ESPN team schedule and game summary endpoints",
        "refreshPolicy": "Scores and game facts only. Rankings and model snapshots update weekly.",
        "games": sorted(events.values(), key=lambda row: (row["date"], row["id"])),
    }
    if old and canonical(old) == canonical(payload):
        print(json.dumps({"changed": False, "games": len(events), "detailsFetched": len(details_needed)}))
        return
    destination.write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    print(json.dumps({"changed": True, "games": len(events), "detailsFetched": len(details_needed), "path": str(destination)}))


if __name__ == "__main__":
    main()
