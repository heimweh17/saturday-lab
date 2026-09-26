"""Fetch the operational inputs used by the scheduled weekly v6 refresh.

Research inputs remain hash-pinned.  This separate cache intentionally follows the
upstream releases so newly completed games can enter the next weekly snapshot.
"""
from __future__ import annotations

import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from pipeline import BASE, ROOT, SOURCES, YEARS

CACHE = ROOT / "analytics" / "production-cache"


def fetch(url: str, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Saturday-Lab/6 weekly-refresh"})
    with urllib.request.urlopen(request, timeout=120) as response:
        body = response.read()
    if len(body) < 100:
        raise RuntimeError(f"Unexpectedly small source: {url}")
    path.write_bytes(body)
    return {"file": str(path.relative_to(CACHE)).replace("\\", "/"), "url": url, "bytes": len(body)}


def main() -> None:
    jobs: list[tuple[str, Path]] = []
    for year in YEARS:
        for kind, (release, name) in SOURCES.items():
            jobs.append((f"{BASE}{release}/{name}_{year}.csv", CACHE / "core" / f"{kind}_{year}.csv"))
        jobs.append((f"{BASE}espn_cfb_adv_team_gamelog/adv_team_gamelog_{year}.csv", CACHE / "advanced" / f"adv_team_gamelog_{year}.csv"))
        jobs.append((f"{BASE}cfb_team_talent/cfb_team_talent_{year}.parquet", CACHE / "advanced" / f"cfb_team_talent_{year}.parquet"))
        jobs.append((f"{BASE}espn_cfb_player_box/player_box_{year}.parquet", CACHE / "roster" / f"player_box_{year}.parquet"))
    for year in range(2014, 2027):
        jobs.append((f"{BASE}cfb_recruits/cfb_recruits_{year}.parquet", CACHE / "roster" / f"cfb_recruits_{year}.parquet"))
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(lambda pair: fetch(*pair), jobs))
    manifest = {
        "retrievedAt": datetime.now(timezone.utc).isoformat(),
        "policy": "Operational rolling inputs. Frozen research manifests remain separate and are never overwritten.",
        "sources": rows,
    }
    (CACHE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    roster_sources = [{"file": Path(row["file"]).name, "url": row["url"]} for row in rows if row["file"].startswith("roster/cfb_recruits_")]
    (CACHE / "roster" / "sources.json").write_text(json.dumps(roster_sources, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(rows), "bytes": sum(row["bytes"] for row in rows)}))


if __name__ == "__main__":
    main()
