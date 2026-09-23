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
- Follow weekly ranking history and separate a team’s own strength update from movement elsewhere in the field.
- Audit every annual candidate, reconstructed prediction, calibration bin and benchmark result; export CSVs.

Results cover 2018–2026. Current results end September 20, 2026; schedules were retrieved September 22. This is a versioned snapshot, **not an automatically updated live service**.

## One production model

Version 5 publishes one scalar neutral-field strength per team:

`P(A wins) = logistic(S(A) - S(B) + venue + rest)`.

Opponent-adjusted offense and defense are fitted jointly, with regularization toward `carry × last season final rating + recruiting weight × standardized recruiting proxy`. Recruiting affects that prior, not a separate opponent-dependent weekly bonus. The ranking averages neutral win probabilities across all FBS opponents and has the same order as scalar strength.

Four documented, retrospective research stages tested **432 additive-recruiting configurations**, **576 recruiting-prior configurations**, **1,056 cohort/efficiency configurations**, then **96 passer-context combinations per annual search** using three earlier-validation-selected rating designs. We compared no talent, equal classes, reduced freshman weight, no freshmen and lagged classes; raw/bounded margins, mismatch weighting, EPA, non-explosive EPA, turnovers, Elo and previous-season observed-passer performance. More variables were not automatically retained.

For each outer season, choose by pooled previous-three-year log loss. Each inner-year coefficient fit trains only on preceding years. Refit through outerYear-1. FPI ranks never enter selection. Current selection: **scoring + prior observed-passer efficiency + venue/rest**, 65% carry, rating penalty 2, published four-class recruiting proxy at 4 points per standard deviation, uniform game weights, regression penalty 1. Prior passer efficiency is shrunk previous-season adjusted yards/attempt, weighted by the most recently observed passers' attempt shares; not future starter knowledge or ESPN QBR.

### Evidence and limits

| Outer season | Games | V5 accuracy | V4 accuracy | Original accuracy | V5 log loss | V4 log loss |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 792 | 72.85% | 73.48% | 72.85% | .52841 | .53609 |
| 2024 | 798 | 69.17% | 68.55% | 68.67% | .55407 | .54966 |
| 2025 | 808 | 72.40% | 73.02% | 72.15% | .53204 | .53511 |
| 2026 partial | 157 | 82.17% | 81.53% | 82.17% | .42845 | .43328 |

2024–25: v5 and v4 both pick **1,137/1,606** winners; original picks 1,131. Pooled log loss is **.54298 (v5), .54234 (v4), .54654 (original)**. V5 is slightly worse than v4 on pooled probability error and better than the original. Current partial season: 129 correct versus v4's 128. This is not uniform superiority or a pristine holdout. Development has inspected these seasons; upstream historical inputs can be revised. Descriptive week-bootstrap intervals and unfavorable subgroup results are published in the model audit.

Recruiting-age ablations do **not** establish that ignoring freshmen is better: the published proxy narrowly wins the current earlier-year validation comparison before the final passer search. Signed-class records do not establish actual redshirts, transfers or playing time. Unreliable game-roster participation flags and same-season returning-production archives were excluded. See `analytics/REVIEW-RESULTS.md` and the four research blueprints.

Current whole-field FPI mean rank gap changes **8.68 → 7.59**, Spearman **.954 → .967**. Model cutoff is September 20; FPI reference September 22. This is diagnostic, not a tuning target or proof of predictive superiority. Historical timestamp-matched FPI-based picks are our calculations with three home points, not official ESPN game probabilities. Archived v3/v4, all preliminary experiments and all final predictions remain downloadable.

## Data and boundaries

- Historical schedules, membership and box scores: [SportsDataverse releases](https://github.com/sportsdataverse/sportsdataverse-data/releases).
- Published future schedules: public ESPN team schedule endpoint, queried for all 138 FBS teams with event-ID deduplication and coverage logging.
- Both have ESPN upstream; they are not independent sources corroborating one another.
- FCS games appear in records and box views but not in scoring/EPA/Elo fits or backtest metrics; they can establish observed passer identity; no FCS probability is fabricated.
- Rate summaries use aggregate numerators/denominators. Missing and zero-attempt rates remain missing. Pass + rush attempts is explicitly a play-volume proxy.
- EPA game logs come from the public cfbfastR pipeline; recruiting is a four-signed-class proxy, not a transfer-adjusted roster. Observed passers use only previous-season efficiency, linked after a completed game; there is no verified future starter, injury, coaching, weather, betting-line or garbage-time correction. Missing EPA pairs are omitted; missing talent is explicitly flagged.
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
# The committed model-v4.json preserves the old baseline for these studies.
python analytics/fetch_extended.py
python analytics/ranking_review.py --data analytics/raw
python analytics/prior_review.py --data analytics/raw
python analytics/cohort_review.py --data analytics/raw
python analytics/qb_review.py --data analytics/raw
python analytics/export_ranking_review.py
python analytics/service_index.py
python analytics/provenance.py --data analytics/raw
python -m unittest discover -s analytics -p 'test*.py' -v
node scripts/check-model.mjs
npm run build:pages
```

The first pipeline regenerates the original benchmark; `final_model.py` recreates v3, and `redesign.py` recreates v4. Then run the four research stages and the final exporter in order. V5 predictions retain `previousProb` (v4), `v3Prob`, and `benchmark` (original); season archives also preserve `baselineProb`. The committed `model-v4.json` is the frozen v4 comparison baseline.

`fetch_redesign.py` verifies 36 pinned source files; `fetch_extended.py` restores and verifies 32 recruiting/player-box/roster investigation files. The research scripts additionally verify 27 normalized core CSV hashes. A mismatch stops reproduction rather than silently mixing revised inputs with cached research. Fresh source revisions require a new research version. Core data default to the original local research directory; pass `--data analytics/raw` when reproducing elsewhere. Set `OPENBLAS_NUM_THREADS=1` to avoid excessive small-matrix threading. Final research caches are generated locally and ignored by Git; selected states, predictions, protocols, source hashes and reports are published.

Schedules are separately refreshed by `fixtures.py`. No API key is required for these endpoints; availability and schemas can change. The site is a dated snapshot, not scheduled live ingestion.

## Tests and implementation

- Python unit tests: future-score/box perturbations, frozen-week boundaries, ridge vs independent least squares, logistic Newton fit vs SciPy BFGS, missing denominators, fixture coverage, all exported probabilities, ranks and record counts.
- Shared-formula test: 2,555 published Python predictions reproduced by the TypeScript implementation; complementary probabilities; exact win-count distribution compared with exhaustive outcome enumeration.
- Optional API checks: `python analytics/check_api.py http://localhost:3000`.
- UI checked on desktop and 390px mobile: schedule, metric selection, past game details, before-week empty states, matchup swapping and audit navigation.

Key files: `analytics/ranking_review.py`, `analytics/cohort_review.py`, `analytics/qb_review.py`, `analytics/export_ranking_review.py`, `lib/model.ts`, `app/forecast.tsx`, `app/data-explorer.tsx`, `app/model-audit.tsx`.

### Data endpoints on Pages

`/saturday-lab/data/2026.json`, `/saturday-lab/data/box-2026.json`, `/saturday-lab/data/model.json`, `/saturday-lab/data/fixtures.json`, `/saturday-lab/data/model-predictions.csv`.

### Portfolio description

Built a reproducible NCAA football analytics application spanning nine seasons, with opponent-adjusted ratings, four-stage retrospective research with nested temporal selection, recruiting-age ablations and observed-passer context, game-level data exploration and remaining-schedule probability forecasts. Published complete backtests and calibration diagnostics, including limitations and comparisons that did not favor the new model.

Independent personal project, not affiliated with the NCAA, ESPN or universities. Team names and marks belong to their respective owners.

To publish a freshly built artifact with an authenticated Git credential helper, run `node scripts/publish-pages.mjs`. The `gh-pages` branch is the configured Pages source; each artifact push triggers publication. Exact raw-source URLs and checksums are in `public/data/provenance.json`.
