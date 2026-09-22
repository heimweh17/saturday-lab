# Saturday Lab

NCAA football analytics: one opponent-adjusted model, transparent temporal validation and an inspectable game-data workbench.

**Website:** https://heimweh17.github.io/saturday-lab/  
**Source:** https://github.com/heimweh17/saturday-lab

## What you can do

- Rank 138 current FBS teams by model-average neutral win probability against the entire field.
- Select historical seasons and before-week snapshots, filter conferences, compare scoring offense/defense and export rankings.
- Open a team’s remaining schedule: projected win/loss, win chance, expected remaining wins and an exact remaining-win distribution under fixed-strength/independence assumptions.
- Select among 30 raw and derived box metrics, switch team/opponent views, filter home/away/FBS games, compare against FBS team averages and inspect complete past-game box scores.
- Compare two teams and venues, inspect probability contributions and scoring-component margin decomposition.
- Audit every annual candidate, held-forward prediction, calibration bin and benchmark result; export CSVs.

Results cover 2018–2026. Current results end September 20, 2026; schedules were retrieved September 22. This is a versioned snapshot, **not an automatically updated live service**.

## One production model

Version 3 publishes a single probability:

`P(win) = w * logistic(beta · x) + (1-w) * logistic(adjusted scoring margin / 8)`.

The ensemble’s components are internal. There is no visitor-facing model switch.

The scoring anchor jointly estimates offense and opponent defense with ridge shrinkage 5, home margin 3, weekly decay .94 and offseason carryover .65. Ten box metrics receive separate opponent adjustment. Eighteen candidate inputs cover scoring, Elo, passing/rushing efficiency, conversion rates, turnovers, play volume, completion, first downs, penalties, possession, form, schedule, experience, rest and interactions.

For each target year, **73 fixed configurations** are compared on the preceding three years. Each inner validation year trains only on earlier seasons. The selected specification is refitted through the year before the target season. Within each season, all team states are frozen before a whole week and updated afterward.

`analytics/final-protocol.json` is written before evaluation and locks the search. Current 2026 selection is the matchup input bundle, ridge 1, and efficiency/scoring weights .5/.5. The model report records all annual choices. Do not change this protocol to chase a particular evaluation result; create a separately documented new version.

### Evidence, not exaggerated claims

| Outer season | FBS games | Winner accuracy | Brier | Log loss |
|---|---:|---:|---:|---:|
| 2024 | 798 | 68.17% | .19129 | .55904 |
| 2025 | 808 | 72.52% | .18142 | .53767 |
| 2026, partial | 157 | 80.25% | .14944 | .46912 |

All results are **retrospective forward backtests**, not forecasts actually published before kickoff. Historical seasons were inspected during development. The richer model does not consistently outperform the original scoring benchmark; that comparison and week-cluster bootstrap intervals are published. The 2018–2022 archive remains exploratory scoring-model history. No performance improvement is claimed merely because more features were added.

## Data and boundaries

- Historical schedules, membership and box scores: [SportsDataverse releases](https://github.com/sportsdataverse/sportsdataverse-data/releases).
- Published future schedules: public ESPN team schedule endpoint, queried for all 138 FBS teams with event-ID deduplication and coverage logging.
- Both have ESPN upstream; they are not independent sources corroborating one another.
- FCS games appear in records and box views but not in rating fits or backtest metrics; no FCS probability is fabricated.
- Rate summaries use aggregate numerators/denominators. Missing and zero-attempt rates remain missing. Pass + rush attempts is explicitly a play-volume proxy.
- No injury, roster availability, transfers, recruiting, weather, betting lines, EPA, true success rate or garbage-time adjustment is claimed.
- Future schedules use fixed current strength and published rest intervals; hypothetical matchups assume equal rest. Win-count distributions assume independent outcomes.

## Run and build

Node 22+ and Python 3.11+ are recommended. Native Next.js is the runtime; legacy Sites/Vinext starter files are not used by these commands.

```sh
npm ci
npm run dev
# Normal Node/Next server build, with optional APIs:
npm run build
npm start
# GitHub Pages build, default base path /saturday-lab:
npm run build:pages
```

On systems with a broken npm shim, invoke the installed `npm-cli.js` with Node directly.

`build:pages` temporarily moves dynamic API routes out of the static build and restores them in a `finally` block. It exports to `out/` with `.nojekyll`. GitHub Pages serves the `gh-pages` branch; the browser calculates from the same shared model implementation. Server APIs are available only in a normal Next deployment, not on Pages.

## Reproduce the analytics

```sh
python -m pip install -r analytics/requirements.txt
python analytics/pipeline.py --data analytics/raw
python analytics/final_model.py --data analytics/raw
python analytics/box_export.py --data analytics/raw
python analytics/fixtures.py
python analytics/service_index.py
python -m unittest discover -s analytics -p 'test*.py' -v
node scripts/check-model.mjs
npm run build:pages
```

The first pipeline regenerates the original locked benchmark. The final model pipeline overlays the unified model on 2023 onward and preserves `baselineProb` for comparison. Raw CSV downloads are cached; changing their contents changes the data version. `fixtures.py` writes fresh published schedule data and preserves retrieval coverage. No API key is required for these endpoints; availability and source schemas can change.

## Tests and implementation

- Python unit tests: future-score/box perturbations, frozen-week boundaries, ridge vs independent least squares, logistic Newton fit vs SciPy BFGS, missing denominators, fixture coverage, all exported probabilities, ranks and record counts.
- Shared-formula test: 2,555 published Python predictions reproduced by the TypeScript implementation; complementary probabilities; exact win-count distribution compared with exhaustive outcome enumeration.
- Optional API checks: `python analytics/check_api.py http://localhost:3000`.
- UI checked on desktop and 390px mobile: schedule, metric selection, past game details, before-week empty states, matchup swapping and audit navigation.

Key files: `analytics/feature_engine.py`, `analytics/final_model.py`, `analytics/final-protocol.json`, `lib/model.ts`, `app/forecast.tsx`, `app/data-explorer.tsx`, `app/model-audit.tsx`.

### Data endpoints on Pages

`/saturday-lab/data/2026.json`, `/saturday-lab/data/box-2026.json`, `/saturday-lab/data/model.json`, `/saturday-lab/data/fixtures.json`, `/saturday-lab/data/model-predictions.csv`.

### Portfolio description

Built a reproducible NCAA football analytics application spanning nine seasons, with opponent-adjusted ratings, nested temporal selection over 73 model configurations, game-level data exploration and remaining-schedule probability forecasts. Published complete backtests and calibration diagnostics, including limitations and comparisons that did not favor the new model.

Independent personal project, not affiliated with the NCAA, ESPN or universities. Team names and marks belong to their respective owners.
