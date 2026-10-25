"""Refuse a formal weekly release while weekend results are only partly published.

The live ESPN feed is the freshness reference.  SportsDataverse remains the
model input, so every completed FBS game before the Monday boundary must exist
in all model-critical rolling source files before the weekly build may proceed.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from pipeline import ROOT

EASTERN = ZoneInfo("America/New_York")
SEASON = 2026
CACHE = ROOT / "analytics" / "production-cache"
DATA = ROOT / "public" / "data"


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def weekly_boundary(now: datetime) -> datetime:
    """Return the latest Monday 04:00 ET boundary at or before ``now``."""
    local = now.astimezone(EASTERN)
    days_since_monday = local.weekday()
    monday = local.date() - timedelta(days=days_since_monday)
    boundary = datetime.combine(monday, time(hour=4), EASTERN)
    if local < boundary:
        boundary -= timedelta(days=7)
    return boundary


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=SEASON)
    parser.add_argument("--now", help="ISO timestamp used by tests or manual audits")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Report missing upstream games without blocking an intentional manual release",
    )
    parser.add_argument(
        "--defer-if-incomplete",
        action="store_true",
        help="Treat incomplete upstream data as a successful deferred check and expose ready=false",
    )
    args = parser.parse_args()

    now = parse_timestamp(args.now) if args.now else datetime.now(timezone.utc)
    boundary = weekly_boundary(now)
    live = json.loads((DATA / f"live-{args.season}.json").read_text(encoding="utf-8"))
    season = json.loads((DATA / f"{args.season}.json").read_text(encoding="utf-8"))
    previous_through_raw = season["snapshots"]["99"].get("through")
    previous_through = parse_timestamp(previous_through_raw) if previous_through_raw else datetime.min.replace(tzinfo=timezone.utc)

    expected = {
        game["id"]: game
        for game in live.get("games", [])
        if game.get("fbs")
        and game.get("completed")
        and previous_through < parse_timestamp(game["date"]) < boundary.astimezone(timezone.utc)
    }

    schedule_rows = read_rows(CACHE / "core" / f"schedules_{args.season}.csv")
    schedules = {row["game_id"]: row for row in schedule_rows}
    box_keys = {
        (row["game_id"], row["team_id"])
        for row in read_rows(CACHE / "core" / f"box_{args.season}.csv")
    }
    advanced_rows = read_rows(CACHE / "advanced" / f"adv_team_gamelog_{args.season}.csv")
    advanced = {(row["game_id"], row["team_id"]): row for row in advanced_rows}

    failures: list[dict[str, object]] = []
    for game_id, game in sorted(expected.items(), key=lambda item: item[1]["date"]):
        reasons: list[str] = []
        schedule = schedules.get(game_id)
        if not schedule or schedule.get("status") != "STATUS_FINAL":
            reasons.append("final schedule")
        else:
            if float(schedule["home_score"]) != float(game["hs"]) or float(schedule["away_score"]) != float(game["as"]):
                reasons.append("matching final score")
        for team_id, score in ((game["home"], game["hs"]), (game["away"], game["as"])):
            if (game_id, team_id) not in box_keys:
                reasons.append(f"team box {team_id}")
            advanced_row = advanced.get((game_id, team_id))
            if advanced_row is None:
                reasons.append(f"advanced row {team_id}")
            else:
                try:
                    if float(advanced_row["points_for"]) != float(score):
                        reasons.append(f"matching advanced score {team_id}")
                except (KeyError, TypeError, ValueError):
                    reasons.append(f"advanced score {team_id}")
        if reasons:
            failures.append({
                "id": game_id,
                "matchup": f"{game['awayName']} at {game['homeName']}",
                "missing": reasons,
            })

    report = {
        "status": "ready" if not failures else "waiting-for-upstream",
        "previousSnapshotThrough": previous_through_raw,
        "weeklyBoundary": boundary.isoformat(),
        "completedFbsGamesExpected": len(expected),
        "incompleteGames": failures,
    }
    print(json.dumps(report, indent=2))

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("### Weekly source readiness\n")
            summary.write(f"- Weekly boundary: `{boundary.isoformat()}`\n")
            summary.write(f"- New completed FBS games expected: `{len(expected)}`\n")
            summary.write(f"- Incomplete upstream games: `{len(failures)}`\n")

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        ready = not failures or args.allow_partial
        with open(output_path, "a", encoding="utf-8") as output:
            output.write(f"ready={'true' if ready else 'false'}\n")

    if failures and not args.allow_partial:
        message = (
            "SportsDataverse has not published every completed weekend FBS game yet; "
            "the formal snapshot was not changed and the automated backstop will retry."
        )
        if args.defer_if_incomplete:
            print(message)
            return
        raise SystemExit(message)


if __name__ == "__main__":
    main()
