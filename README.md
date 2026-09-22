# Saturday Lab

A college-football analytics portfolio project with a working web application, server APIs and a reproducible Python modeling pipeline.

## What works

- Nine seasons, 2018–2026; current snapshot ends September 20, 2026.
- National FBS power rankings by historical week, conference and team search.
- Opponent-adjusted offense and defense; strength-of-schedule context.
- Team scouting reports, rank/strength history, real box scores and game logs.
- Two-team comparison, neutral/home venue simulation, probability and margin decomposition.
- Week-forward prediction ledger, mistakes/upsets filters, CSV exports.
- Validation grid, Elo/50–50 baselines, holdout metrics and probability calibration.
- Read-only HTTP APIs, input validation and browser WebMCP tools.

The data is a versioned snapshot. No automatic refresh or live feed is claimed.

## Results

The scoring model was selected on 2023 log loss from 36 scoring settings. An Elo benchmark used 12 settings, followed by 5 blend weights. The winning blend has Elo weight zero, so the public ranking is the opponent-adjusted scoring model.

Locked 2024–2025 holdout: 1,606 FBS games, 70.42% winner accuracy, Brier score 0.18572, log loss 0.54654, margin MAE 12.71 points. These are retrospective estimates, not forecasts actually published at the time.

## Run locally

Requirements: Node 22.13+ and Python 3.10+ with NumPy.

```sh
npm ci
npm run dev
```

Open the URL printed by the server. On Windows, if an npm shim resolves incorrectly, invoke the installed npm JavaScript entrypoint with node.

```sh
python -m pip install -r analytics/requirements.txt
python analytics/pipeline.py
python analytics/service_index.py
python -m unittest discover -s analytics -p 'test_*.py'
npx tsc --noEmit
npm run build
npm start
```

The pipeline downloads public CSVs only when missing. For a refresh, remove the cached files for the season you intend to refresh, then rerun. The checked-in `analytics/locked-config.json` keeps model settings frozen. Do not remove it to optimize against the existing holdout; a new model experiment requires a fresh validation design and version label.

To use an already downloaded dataset, pass `--data PATH` to pipeline.py. Expected names: schedules_YEAR.csv, teams_YEAR.csv and box_YEAR.csv. Raw data is ignored by Git; exported analysis snapshots are included.

## Source map

- `analytics/pipeline.py`: ingestion, filters, ridge coordinate descent, Elo, grid search and snapshot export.
- `analytics/locked-config.json`: versioned hyperparameters and 2023 candidate results.
- `analytics/test_model.py`: independent ridge solver agreement, future-outcome invariance, batch ordering, neutral symmetry, metrics and every snapshot's coverage/records.
- `analytics/service_index.py`: compact ratings index for the server.
- `lib/predict.ts`: shared matchup mathematics.
- `app/api/`: server ratings, matchup and health endpoints.
- `app/`: frontend, scouting, matchup, audit and methodology.
- `public/data/`: season snapshots, manifest/checksums, model report and prediction CSV.

## Mathematical details

Per team/game score = mu + offense - opponent defense + H*venue. Venue is +0.5 for home, -0.5 for away, zero for neutral. Ridge shrinks offensive and defensive components to 65% of prior-season final ratings. The mean scoring prior is 28 with weight 20. Selected lambda=2, H=2 points, recency decay=1. Power=offense+defense; win probability=logistic(expected margin / 8).

Every week is a frozen batch. No target-week score influences a target-week forecast. Team statistics also use only games before the selected week. 2018–2022 warm up the model, 2023 selects parameters, 2024–2025 are untouched for parameter selection. Holdout ratings update using earlier holdout games as in deployment. Historical score corrections can affect retrospective results.

Only completed season-type 2/3 games enter analysis. FBS membership is per season, excluding all-star/exhibition teams. Records include non-FBS opponents; ratings and evaluation only include FBS vs. FBS. Offense/defense are scoring effects, not pure unit efficiency, EPA, success rate or per-drive performance. No injuries, roster changes, pace or garbage-time corrections are modeled.

## API

- GET /api/health
- GET /api/ratings?season=2026&week=99
- GET /api/matchup?season=2026&week=99&a=194&b=333&venue=neutral
- GET /data/2025.json
- GET /data/report.json
- GET /data/predictions.csv

Team IDs follow ESPN. Venue accepts a, b or neutral. Week 99 means latest available; other week keys are before-week states. Postseason keys add 30 to the source week. Invalid inputs receive 400 responses. API ratings are rounded to three decimal places; the historical prediction CSV retains full model precision.

## Data attribution

Source: https://github.com/sportsdataverse/sportsdataverse-data

Releases: espn_cfb_schedules/cfb_schedule_YEAR.csv, espn_cfb_teams/cfb_teams_YEAR.csv, espn_cfb_team_box/team_box_YEAR.csv. SportsDataverse processes ESPN-derived data. University logos are fetched from the source's ESPN logo URLs. Saturday Lab is independent and not affiliated with NCAA, ESPN, SportsDataverse or universities. Upstream content retains its respective rights; attribution is not a claim of endorsement.

## Hosting

The Vinext/React application builds to a Cloudflare-compatible Worker plus static assets. The Sites project identifier is in .openai/hosting.json. No paid data key, secret, external database or user login is required by this application. No credentials are included in the source package.

## Future work

Add genuine play-by-play EPA and success rate, roster continuity and player availability, nested rolling validation, an untouched future-season evaluation, and automated refresh with observed freshness checks. These are future work, not implemented features.
