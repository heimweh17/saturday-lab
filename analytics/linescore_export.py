"""Download and validate ESPN-derived period scores for the published game archive."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "public" / "data"
YEARS = range(2018, 2027)
API = "https://api.github.com/repos/sportsdataverse/sportsdataverse-data/releases/tags/espn_cfb_linescores"
USER_AGENT = "Saturday-Lab linescore archive"


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def main() -> None:
    release = json.loads(get(API))
    assets = {asset["name"]: asset for asset in release["assets"]}
    source_records = []
    for year in YEARS:
        name = f"linescores_{year}.csv"
        asset = assets[name]
        raw = get(asset["browser_download_url"])
        sha256 = hashlib.sha256(raw).hexdigest()
        rows_by_game: dict[str, dict[str, list[tuple[int, int]]]] = {}
        for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
            game_id, team_id = str(row["game_id"]), str(row["team_id"])
            rows_by_game.setdefault(game_id, {}).setdefault(team_id, []).append((int(row["period"]), int(float(row["value"]))))

        season = json.loads((DATA / f"{year}.json").read_text(encoding="utf-8"))
        archive_games = season["games"]
        output: dict[str, dict[str, list[int]]] = {}
        mismatches = 0
        for game in archive_games:
            game_id = str(game["id"])
            team_rows = rows_by_game.get(game_id, {})
            away_rows, home_rows = team_rows.get(str(game["away"])), team_rows.get(str(game["home"]))
            if not away_rows or not home_rows:
                continue
            away = [value for _, value in sorted(away_rows)]
            home = [value for _, value in sorted(home_rows)]
            if sum(away) != int(game["as"]) or sum(home) != int(game["hs"]):
                mismatches += 1
                continue
            output[game_id] = {"away": away, "home": home}

        payload = {
            "season": year,
            "source": "SportsDataverse espn_cfb_linescores (ESPN-derived)",
            "sourceUpdatedAt": release["published_at"],
            "coverage": {"archiveGames": len(archive_games), "gamesWithValidatedPeriods": len(output), "rejectedTotalMismatches": mismatches},
            "games": output,
        }
        (DATA / f"periods-{year}.json").write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        source_records.append({"season": year, "asset": name, "url": asset["browser_download_url"], "sha256": sha256, "bytes": len(raw), **payload["coverage"]})
        print(f"{year}: {len(output)}/{len(archive_games)} games, {mismatches} total mismatches")

    provenance = {"releaseTag": release["tag_name"], "releasePublishedAt": release["published_at"], "releaseUrl": release["html_url"], "assets": source_records}
    provenance_text = json.dumps(provenance, indent=2) + "\n"
    (ROOT / "analytics" / "linescore-sources.json").write_text(provenance_text, encoding="utf-8")
    (DATA / "linescore-sources.json").write_text(provenance_text, encoding="utf-8")


if __name__ == "__main__":
    main()
