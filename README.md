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

Version 4 publishes `P(win) = logistic(beta * pregame features)`, one probability and one ranking.

The redesign compares **288 configurations**: 24 scoring-rating designs x six feature bundles x two regularization penalties. Designs test raw, clipped and smoothly compressed margins; 40%/65% carry; one/three prior seasons; weak/strong prior penalties. Bundles test scoring, opponent-adjusted total/passing/rushing EPA, special teams, yards per play, recruiting talent, rest, venue and nonlinear terms.

Each target season selects by pooled log loss over its preceding three seasons. Every inner year itself trains only on prior years. Current selection: raw-score ratings, 65% carry, one prior year, rating penalty 4, EPA + talent bundle, regression penalty 1. The complete protocol is `analytics/redesign-protocol.json`. FPI ranks never enter training or selection.

### Evidence and limits

| Outer season | Games | New accuracy | Previous v3 | New log loss | V3 log loss |
|---|---:|---:|---:|---:|---:|
| 2023 | 792 | 73.48% | 72.98% | .53609 | .54134 |
| 2024 | 798 | 68.55% | 68.17% | .54966 | .55904 |
| 2025 | 808 | 73.02% | 72.52% | .53511 | .53767 |
| 2026 partial | 157 | 81.53% | 80.25% | .43328 | .46912 |

2024-25 pooled log-loss improvement has a descriptive week-bootstrap interval crossing zero. 2025 late-season loss is worse than v3. The original scoring model still beats v4 on some measures. Historical FPI-based picks outperform v4 in 2024/2025 matched samples; these are our picks from timestamped FPI + three home points, not ESPN official probabilities. No claim of outperforming ESPN is made.

Current whole-field rank agreement with FPI improves (mean gap 11.84 to 8.68 places, Spearman .920 to .954). Model results end September 20; FPI reference is September 22. This comparison is diagnostic, not a tuning target.

All tests are retrospective. Upstream EPA estimation may reflect later data, and development has inspected these seasons. Missing talent now uses an FBS mean and explicit indicator; the preliminary zero-imputation experiment was superseded before publication. Returning-production data were excluded because same-season participation cannot establish preseason availability. Archived v3 remains in `public/data/model-v3.json`; the earlier carry-only study remains downloadable.

## Data and boundaries

- Historical schedules, membership and box scores: [SportsDataverse releases](https://github.com/sportsdataverse/sportsdataverse-data/releases).
- Published future schedules: public ESPN team schedule endpoint, queried for all 138 FBS teams with event-ID deduplication and coverage logging.
- Both have ESPN upstream; they are not independent sources corroborating one another.
- FCS games appear in records and box views but not in rating fits or backtest metrics; no FCS probability is fabricated.
- Rate summaries use aggregate numerators/denominators. Missing and zero-attempt rates remain missing. Pass + rush attempts is explicitly a play-volume proxy.
- EPA game logs come from the public cfbfastR pipeline; recruiting is a four-signed-class proxy, not a transfer-adjusted roster. No verified injury, quarterback, coaching, weather, betting-line or garbage-time correction is claimed. Missing EPA pairs are omitted; missing talent is explicitly flagged.
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
python analytics/fetch_redesign.py
python analytics/redesign.py --data analytics/raw
python analytics/export_redesign.py
python analytics/service_index.py
python analytics/provenance.py --data analytics/raw
python -m unittest discover -s analytics -p 'test*.py' -v
node scripts/check-model.mjs
npm run build:pages
```

The first pipeline regenerates the original locked benchmark. The old final-model pipeline recreates v3. The redesign then selects and exports v4; run the commands in order. `baselineProb` preserves v1 and `previousProb` preserves v3. `fetch_redesign.py` verifies 36 source files against pinned hashes and refuses silently revised inputs. Raw CSV downloads are cached; changing their contents changes the data version. `fixtures.py` writes fresh published schedule data and preserves retrieval coverage. No API key is required for these endpoints; availability and source schemas can change.

## Tests and implementation

- Python unit tests: future-score/box perturbations, frozen-week boundaries, ridge vs independent least squares, logistic Newton fit vs SciPy BFGS, missing denominators, fixture coverage, all exported probabilities, ranks and record counts.
- Shared-formula test: 2,555 published Python predictions reproduced by the TypeScript implementation; complementary probabilities; exact win-count distribution compared with exhaustive outcome enumeration.
- Optional API checks: `python analytics/check_api.py http://localhost:3000`.
- UI checked on desktop and 390px mobile: schedule, metric selection, past game details, before-week empty states, matchup swapping and audit navigation.

Key files: `analytics/redesign.py`, `analytics/export_redesign.py`, `analytics/redesign-protocol.json`, `lib/model.ts`, `app/forecast.tsx`, `app/data-explorer.tsx`, `app/model-audit.tsx`.

### Data endpoints on Pages

`/saturday-lab/data/2026.json`, `/saturday-lab/data/box-2026.json`, `/saturday-lab/data/model.json`, `/saturday-lab/data/fixtures.json`, `/saturday-lab/data/model-predictions.csv`.

### Portfolio description

Built a reproducible NCAA football analytics application spanning nine seasons, with opponent-adjusted ratings, nested temporal selection over 288 model configurations, game-level data exploration and remaining-schedule probability forecasts. Published complete backtests and calibration diagnostics, including limitations and comparisons that did not favor the new model.

Independent personal project, not affiliated with the NCAA, ESPN or universities. Team names and marks belong to their respective owners.

To publish a freshly built artifact with an authenticated Git credential helper, run `node scripts/publish-pages.mjs`. The `gh-pages` branch is the configured Pages source; each artifact push triggers publication. Exact raw-source URLs and checksums are in `public/data/provenance.json`.
