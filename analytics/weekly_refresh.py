"""Build the current-season weekly snapshot with the frozen v6 specification."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import box_export
import cohort_review as cohort
import qb_review as qb
import ranking_review as rating
from pipeline import ROOT, box_summary, load_data, metrics, sigmoid

SEASON = 2026
CACHE = ROOT / "analytics" / "production-cache"
DATA = ROOT / "public" / "data"


def number(row: dict, key: str) -> float | None:
    try:
        value = float(row[key])
        return value if np.isfinite(value) else None
    except (KeyError, TypeError, ValueError):
        return None


def quarantine_inconsistent_current_games() -> list[str]:
    """Keep an upstream mid-refresh race out of the formal weekly snapshot."""
    schedule_path = CACHE / "core" / f"schedules_{SEASON}.csv"
    advanced_path = CACHE / "advanced" / f"adv_team_gamelog_{SEASON}.csv"
    with schedule_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle)); fields = list(rows[0])
    advanced = {}
    with advanced_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            advanced[(row["game_id"], row["team_id"])] = number(row, "points_for")
    rejected = []
    for row in rows:
        if row.get("status") != "STATUS_FINAL":
            continue
        expected = ((row["home_id"], number(row, "home_score")), (row["away_id"], number(row, "away_score")))
        observed = [advanced.get((row["game_id"], team)) for team, _ in expected]
        if all(value is not None for value in observed) and any(observed[i] != expected[i][1] for i in range(2)):
            row["status"] = "STATUS_IN_PROGRESS"
            rejected.append(row["game_id"])
    if rejected:
        with schedule_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
        print(json.dumps({"quarantinedUpstreamRaces": rejected}))
    return rejected


def build_states():
    quarantine_inconsistent_current_games()
    rating.SOURCE_DATA = CACHE / "core"
    rating.DIR = CACHE / "advanced"
    cohort.DATA = CACHE / "roster"
    rating.verify_files = lambda *_: None
    cohort.r.verify_files = lambda *_: None
    cohort.configure()
    production = json.loads((ROOT / "lib" / "production-config.json").read_text(encoding="utf-8"))
    rating.NAMES = production["featureNames"]
    rating.UNIT_INDICES = list(range(9))
    teams, seasons, talents, coverage = cohort.read_inputs()
    for year in rating.YEARS:
        raw = list(csv.DictReader((rating.DIR / f"adv_team_gamelog_{year}.csv").open(encoding="utf-8-sig")))
        lookup = {(row["game_id"], row["team_id"]): row for row in raw}
        for game in seasons[year]["games"]:
            for index, team in enumerate((game["home"], game["away"])):
                row = lookup.get((game["id"], team), {})
                game["units"][index].extend([
                    number(row, "first_downs_created_rate"),
                    number(row, "EPA_passing_per_play"),
                    number(row, "EPA_rushing_per_play"),
                    number(row, "yards_per_play"),
                    number(row, "EPA_explosive_rate"),
                ])
    config = production
    states = cohort.build(teams, seasons, talents, config["selected"]["ratingConfig"])
    _, _, boxes, audit = load_data(CACHE / "core")
    passers, passer_coverage = qb.passer_states(teams, seasons, boxes)
    for key, snapshot in states.items():
        for team, state in snapshot.items():
            state["q"].extend(passers[key][team]["values"])
            state["passerContext"] = passers[key][team]
    return teams, seasons, boxes, audit, coverage, passer_coverage, states, config


def probability(game: dict, states: dict, coef: np.ndarray) -> float:
    snapshot = states[f'{SEASON}:{game["week"]}']
    values = rating.features(
        snapshot[game["home"]], snapshot[game["away"]],
        0 if game["neutral"] else 1, "broad", game["date"],
    )
    return float(sigmoid(np.asarray(values) @ coef))


def archive_live_periods() -> None:
    live_path = DATA / f"live-{SEASON}.json"
    period_path = DATA / f"periods-{SEASON}.json"
    if not live_path.exists() or not period_path.exists():
        return
    live = json.loads(live_path.read_text(encoding="utf-8"))
    periods = json.loads(period_path.read_text(encoding="utf-8"))
    rows = dict(periods.get("games", {}))
    for game in live.get("games", []):
        detail = game.get("detail") or {}
        if not game.get("completed") or not detail.get("periods"):
            continue
        rows[game["id"]] = detail["periods"]
    periods["games"] = dict(sorted(rows.items()))
    periods["sourceUpdatedAt"] = live.get("updatedAt")
    period_path.write_text(json.dumps(periods, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    teams, seasons, boxes, audit, coverage, passer_coverage, states, production = build_states()
    coef = np.asarray(production["coefficients"])
    old = json.loads((DATA / f"{SEASON}.json").read_text(encoding="utf-8"))
    old_predictions = {row["id"]: row for row in old.get("predictions", [])}
    season = seasons[SEASON]
    predictions = []
    week_cutoffs = {week: min(game["date"] for game in season["games"] if game["week"] == week) for week in season["weeks"]}
    for game in season["games"]:
        if not game["fbs"]:
            continue
        p = probability(game, states, coef)
        archived = old_predictions.get(game["id"], {})
        state = states[f'{SEASON}:{game["week"]}']
        home, away = state[game["home"]], state[game["away"]]
        margin = home["q"][0] - away["q"][0] + (0 if game["neutral"] else 3.0)
        total = 2 * home["mu"] + home["offense"] - away["defense"] + away["offense"] - home["defense"]
        predictions.append({
            **game,
            "margin": float(margin), "homeScore": float((total + margin) / 2), "awayScore": float((total - margin) / 2),
            "prob": float(archived.get("prob", p)), "outcome": int(game["hs"] > game["as"]),
            "cutoff": archived.get("cutoff", week_cutoffs[game["week"]]),
            "modelVersion": archived.get("modelVersion", "6.0.0"),
        })
    snapshots, previous_ranks, previous_strength, previous_index = {}, {}, {}, {}
    for week in season["weeks"] + [99]:
        prior_weeks = season["weeks"][:season["weeks"].index(week)] if week != 99 else season["weeks"]
        past = [game for game in season["games"] if game["week"] in prior_weeks]
        source = states[f"{SEASON}:{week}"]
        strength = {team: float(np.asarray(state["q"]) @ coef[:-2]) for team, state in source.items()}
        index = {team: float(np.mean([sigmoid(value - other) for opponent, other in strength.items() if opponent != team])) for team, value in strength.items()}
        order = sorted(strength, key=lambda team: (-strength[team], team))
        ranks = {team: rank for rank, team in enumerate(order, 1)}
        old_snapshot = old.get("snapshots", {}).get(str(week), old["snapshots"]["99"])
        old_teams = {team["id"]: team for team in old_snapshot["teams"]}
        rows = []
        for team_id, identity in teams[SEASON].items():
            state = source[team_id]
            games = [game for game in past if team_id in (game["home"], game["away"])]
            fbs_games = [game for game in games if game["fbs"]]
            wins = sum((game["hs"] > game["as"]) == (game["home"] == team_id) for game in games)
            pf = [game["hs"] if game["home"] == team_id else game["as"] for game in games]
            pa = [game["as"] if game["home"] == team_id else game["hs"] for game in games]
            opponents = [strength[game["away"] if game["home"] == team_id else game["home"]] for game in fbs_games]
            prior = old_teams.get(team_id, {})
            row = {
                **prior, **identity,
                "offense": state["offense"], "defense": state["defense"], "power": state["q"][0],
                "elo": 1500 + state["q"][3] * 100, "wins": wins, "losses": len(games) - wins,
                "games": len(games), "modelGames": len(fbs_games),
                "pf": round(float(np.mean(pf)), 2) if pf else None, "pa": round(float(np.mean(pa)), 2) if pa else None,
                "sos": round(float(np.mean(opponents)), 3) if opponents else None,
                **box_summary(games, team_id, boxes[SEASON]),
                "modelState": {**state, "basePower": state["q"][0]},
                "winIndex": index[team_id], "modelRank": ranks[team_id],
                "modelChange": previous_ranks.get(team_id, ranks[team_id]) - ranks[team_id],
            }
            if previous_ranks:
                fixed = float(np.mean([sigmoid(strength[team_id] - value) for opponent, value in previous_strength.items() if opponent != team_id]))
                row["ratingExplanation"] = {"previousRank": previous_ranks[team_id], "ownIndexChange": fixed - previous_index[team_id], "fieldIndexChange": index[team_id] - fixed}
            else:
                row.pop("ratingExplanation", None)
            rows.append(row)
        snapshots[str(week)] = {
            "teams": rows, "mu": next(iter(source.values()))["mu"], "gamesUsed": len(past),
            "modelGames": sum(game["fbs"] for game in past), "through": max((game["date"] for game in past), default=None),
        }
        previous_ranks, previous_strength, previous_index = ranks, strength, index
    payload = {
        "season": SEASON, "weeks": season["weeks"] + [99], "snapshots": snapshots,
        "games": season["games"], "predictions": predictions,
        "model": {**old.get("model", {}), "version": "6.0.0", "coefficients": coef.tolist(), "weeklySnapshot": True},
    }
    (DATA / f"{SEASON}.json").write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    # Export current team box data from the same operational source.
    original_years = box_export.YEARS
    box_export.YEARS = [SEASON]
    import sys
    argv = sys.argv
    try:
        sys.argv = ["box_export.py", "--data", str(CACHE / "core")]
        box_export.main()
    finally:
        sys.argv = argv
        box_export.YEARS = original_years
    archive_live_periods()
    manifest_path = DATA / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generatedAt"] = datetime.now(timezone.utc).isoformat()
    manifest["weeklySnapshotThrough"] = snapshots["99"]["through"]
    manifest["audit"] = [row for row in manifest["audit"] if row["season"] != SEASON] + [next(row for row in audit if row["season"] == SEASON)]
    manifest_path.write_text(json.dumps(manifest, separators=(",", ":")), encoding="utf-8")
    report_path = DATA / "model.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    current_metrics = metrics([row["prob"] for row in predictions], [row["outcome"] for row in predictions])
    report["evaluation"] = [row for row in report["evaluation"] if not (row["season"] == SEASON and row["model"] == "Saturday model v6")]
    report["evaluation"].append({"season": SEASON, "model": "Saturday model v6", **current_metrics})
    report["predictions"] = [row for row in report.get("predictions", []) if row.get("season") != SEASON] + predictions
    report_path.write_text(json.dumps(report, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    print(json.dumps({"season": SEASON, "weeks": season["weeks"], "games": len(season["games"]), "fbsPredictions": len(predictions), "through": snapshots["99"]["through"]}))


if __name__ == "__main__":
    main()
