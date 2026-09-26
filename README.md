# Saturday Lab

College football rankings, team reports, schedule forecasts and matchup analysis powered by one opponent-adjusted model.

**Website:** https://heimweh17.github.io/saturday-lab/

**Source:** https://github.com/heimweh17/saturday-lab

## What you can do

- Scan a Top 25 or search and filter the complete 138-team FBS ranking by model-average neutral win probability against the entire field.
- Open the dedicated team directory to search by school, nickname, abbreviation or conference, or use large quick-access cards for frequently followed programs.
- Start with a weekly matchup board ranked by a documented marquee score: 60% team quality and 40% projected closeness, limited to games with a Top 25 team or two Top 50 teams. Close projections are flagged, and every matchup opens its own game center.
- Open a dedicated scores and schedule center for recent finals or any upcoming week, search the slate by team and see current one-decimal win probabilities before opening a game.
- See the latest movement around the rankings: biggest riser, biggest slide and the leading opponent-adjusted offense and defense.
- Select historical seasons and before-week snapshots, filter conferences, compare scoring offense/defense and export rankings.
- Open a team’s remaining schedule: projected win/loss, win chance, expected remaining wins and an exact remaining-win distribution under fixed-strength/independence assumptions.
- Select among 30 raw and derived box metrics, switch team/opponent views, filter home/away/FBS games, compare against FBS team averages and inspect complete past-game box scores.
- Open any completed game for quarter-by-quarter scoring, a side-by-side team box score including first downs, total/passing/rushing yards, attempts, down conversions, turnovers, penalties and possession, plus linked meetings from the current and previous four seasons. Upcoming game centers show one-decimal probabilities and a broader current-form comparison.
- Search for any two teams, compare venues, inspect probability contributions and see a full-model expected score whose favored team agrees with the published win probability.
- Compare as many as 12 teams on one season-long ranking chart, switch between a fitted view and all FBS ranks, zoom the scale, or follow one team week by week with the game result behind every ranking point.
- Explore every team on a large, expandable offense-versus-defense map with hover details, range controls, wheel/pinch zoom, panning and direct links to team reports.
- Audit every annual candidate, reconstructed prediction, calibration bin and benchmark result; export CSVs.

## Site architecture

Saturday Lab is statically exported as a browsable sports data publication rather than a single tabbed dashboard:

- `/teams/florida-gators/` is a permanent team report with rankings, weekly movement, forecast schedule, past results and box-score-derived splits.
- `/games/` is the current scores and schedule center. It joins recent finals with the published future slate and links every card to a permanent game center.
- `/games/2026/ole-miss-rebels-at-florida-gators-401856699/` is a permanent game center. Upcoming games show the v6 probability, projected score, venue and available event details; completed games preserve the score and the model prediction that existed before kickoff.
- `/matchup/` is reserved for hypothetical simulations. `/rank-trends/` provides multi-team season charts. `/model/`, `/methodology/` and `/legal/` keep model documentation and source terms outside the main data workflow.
- Team and opponent references link back to team reports. The home marquee board and schedule rows link to game centers instead of sending readers to an external site.
- `sitemap.xml` enumerates the complete generated archive and `robots.txt` exposes it to crawlers.

The Pages build currently generates the complete 2018–2026 game archive plus current and historical team-name routes. Completed game centers include validated period scores for every game in that archive. Game weather, television and stadium detail are shown only when the published source includes them; the interface omits unavailable secondary facts instead of inventing values.

Results cover 2018–2026. Current results end September 20, 2026; schedules were retrieved September 22. This is a versioned snapshot, **not an automatically updated live service**.

## Current production model: v6

Every ranking and forecast on the main site uses version 6. It publishes one scalar neutral-field strength per team:

`P(A wins) = logistic(S(A) - S(B) + venue + rest)`.

Opponent-adjusted offense and defense are fitted jointly, with regularization toward `carry × last season final rating + recruiting weight × standardized recruiting proxy`. Recruiting affects that prior, not a separate opponent-dependent weekly bonus. The ranking averages neutral win probabilities across all FBS opponents and has the same order as scalar strength.

Eight documented, retrospective research stages tested recruiting placement, prior strength, roster cohorts, passer history, raw pregame play features, opponent-adjusted replication, the durability of preseason inputs, and the final model's home-field coefficient. Stage 6 compares scoring strength with opponent-adjusted non-explosive EPA, first-down creation, passing EPA, rushing EPA, yards per play and explosive-play rate. The raw success-rate result was not promoted until its signal survived explicit schedule-strength adjustment.

For each outer season, choose by pooled previous-three-year log loss. Each inner-year coefficient fit trains only on preceding years. Refit through outerYear-1. FPI ranks never enter selection. Current selection is the broad opponent-adjusted bundle; its fitted nonzero terms are scoring strength, first-down creation, rushing EPA, yards per play, prior observed-passer efficiency, venue and rest. It retains 65% carry, rating penalty 2, the published recruiting prior at 4 points per standard deviation, uniform game weights and regression penalty 1.

### Evidence and limits

| Outer season | Games | V6 accuracy | V5 accuracy | Original accuracy | V6 log loss | V5 log loss |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 792 | 74.12% | 72.85% | 72.85% | .53238 | .52841 |
| 2024 | 798 | 69.30% | 69.17% | 68.67% | .54709 | .55407 |
| 2025 | 808 | 73.02% | 72.40% | 72.15% | .53025 | .53204 |
| 2026 partial | 157 | 81.53% | 82.17% | 82.17% | .42688 | .42845 |

2024–25: v6 picks **1,143/1,606** winners versus v5's 1,137. Pooled log loss improves **.54298 → .53862**. A prespecified week-block bootstrap favored v6 in **92.9%** of 10,000 resamples, above the 90% promotion threshold, and neither complete season breached the regression guard. The partial 2026 sample improves log loss slightly but has one fewer correct pick. This is retrospective evidence rather than a pristine holdout.

Recruiting-age ablations do **not** establish that ignoring freshmen is better: the published proxy narrowly wins the current earlier-year validation comparison before the final passer search. Signed-class records do not establish actual redshirts, transfers or playing time. Unreliable game-roster participation flags and same-season returning-production archives were excluded. See `analytics/REVIEW-RESULTS.md` and the four research blueprints.

Current whole-field FPI mean rank gap changes **7.59 → 7.57** from v5 to v6, with Spearman **.967 → .968**. Model cutoff is September 20; FPI reference September 22. This is diagnostic, not a tuning target. Archived v3/v4/v5, all preliminary experiments and final predictions remain downloadable.

Stage 7 froze v6, then evaluated 1,215 combinations of efficiency carryover/shrinkage, component bundles, preseason fade, returning production, staff continuity and ridge strength. The best rolling candidate improved pooled 2023–25 log loss by **.00131**, below the **.0015** gate; the week-block bootstrap favored it only **73.1%** of the time, 2024 breached the regression guard, and FPI mean rank gap worsened **7.57 → 9.75**. Returning production showed signal, but no architecture was stable enough to promote. Production remains v6; the full rejected experiment is published as `public/data/research-stage7.json`.

Stage 8 audited the fitted home-field logit coefficient instead of changing it by intuition. The freely fitted value stayed between **.320 and .327** across four successive target-season fits. In 566 completed 2023–25 games where neutralized v6 strength was between 40% and 60%, home teams actually won **57.6%**; v6 predicted **57.9%**. A predeclared comparison selected .30 from fixed alternatives, but it slightly worsened pooled log loss (**.534297 → .534372**) and the week-block bootstrap favored it only **17.9%** of the time. Adding the efficiency inputs moved the coefficient gradually rather than causing a collapse or jump. The audit therefore retained v6's .327 coefficient; full results are in `analytics/HOME-FIELD-AUDIT-RESULTS.md` and `public/data/research-stage8-home-field.json`.

Projected scores use a separate, frozen score layer without changing v6 probabilities. A positive robust fit maps the v6 probability logit to expected margin, while a historical calibration of the opponent-adjusted scoring total estimates game pace. The two expected scores are derived from that margin and total, so the displayed score leader always agrees with the probability leader. Rolling 2023–24 evaluation selected the method; the untouched 2025 test improved margin MAE **12.36 → 12.18**, total MAE **13.19 → 12.94**, and team-score MAE **9.02 → 8.95**. Decimal points are expected values, not literal score picks.

## Data and boundaries

- Historical schedules, membership, box scores and scoring by period: [SportsDataverse releases](https://github.com/sportsdataverse/sportsdataverse-data/releases), derived from ESPN records. Every period-score asset is SHA-256 recorded and totals are checked against the final score before publication.
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
python analytics/linescore_export.py
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
python analytics/stability_review.py
python analytics/opponent_stability_review.py
python analytics/home_field_audit.py
python analytics/full_score_layer.py
python analytics/export_opponent_stability.py
python analytics/service_index.py
python analytics/provenance.py --data analytics/raw
python -m unittest discover -s analytics -p 'test*.py' -v
node scripts/check-model.mjs
npm run build:pages
```

The first pipeline regenerates the original benchmark; `final_model.py` recreates v3, and `redesign.py` recreates v4. Run the research stages in order. The later studies freeze their designs before results, test raw as-of play features, repeat useful signals with opponent adjustment, and audit the durability of preseason information. The committed model-v4/v5 reports preserve comparison baselines.

`fetch_redesign.py` verifies 36 pinned source files; `fetch_extended.py` restores and verifies 32 recruiting/player-box/roster investigation files. The research scripts additionally verify 27 normalized core CSV hashes. A mismatch stops reproduction rather than silently mixing revised inputs with cached research. Fresh source revisions require a new research version. Core data default to the original local research directory; pass `--data analytics/raw` when reproducing elsewhere. Set `OPENBLAS_NUM_THREADS=1` to avoid excessive small-matrix threading. Final research caches are generated locally and ignored by Git; selected states, predictions, protocols, source hashes and reports are published.

Schedules are separately refreshed by `fixtures.py`. No API key is required for these endpoints; availability and schemas can change. The site is a dated snapshot, not scheduled live ingestion.

## Tests and implementation

- Python unit tests: future-score/box perturbations, frozen-week boundaries, ridge vs independent least squares, logistic Newton fit vs SciPy BFGS, missing denominators, fixture coverage, all exported probabilities, ranks and record counts.
- Shared-formula test: 2,555 published Python predictions reproduced by the TypeScript implementation; complementary probabilities; exact win-count distribution compared with exhaustive outcome enumeration.
- Optional API checks: `python analytics/check_api.py http://localhost:3000`.
- UI checked on desktop and 390px mobile: rankings, score center, team report, period scoring, schedule, metric selection, past game details, before-week empty states, matchup swapping and audit navigation.

Key files: `analytics/ranking_review.py`, `analytics/cohort_review.py`, `analytics/qb_review.py`, `analytics/stability_review.py`, `analytics/opponent_stability_review.py`, `analytics/durability_review.py`, `analytics/home_field_audit.py`, `lib/model.ts`, `app/forecast.tsx`, `app/model-audit.tsx`.

### Data endpoints on Pages

`/saturday-lab/data/2026.json`, `/saturday-lab/data/box-2026.json`, `/saturday-lab/data/periods-2026.json`, `/saturday-lab/data/linescore-sources.json`, `/saturday-lab/data/model.json`, `/saturday-lab/data/score-layer.json`, `/saturday-lab/data/fixtures.json`, `/saturday-lab/data/model-predictions.csv`, `/saturday-lab/data/research-stage7.json`, `/saturday-lab/data/research-stage8-home-field.json`.

### Portfolio description

Built a reproducible NCAA football analytics application spanning nine seasons, with opponent-adjusted ratings, seven-stage retrospective research with nested temporal selection, recruiting-age ablations, observed-passer context, game-level data exploration and remaining-schedule probability forecasts. Published complete backtests, promotion gates and calibration diagnostics, including unfavorable comparisons.

Independent personal project, not affiliated with the NCAA, ESPN or universities. Team names and marks belong to their respective owners.

To publish a freshly built artifact with an authenticated Git credential helper, run `node scripts/publish-pages.mjs`. The `gh-pages` branch is the configured Pages source; each artifact push triggers publication. Exact raw-source URLs and checksums are in `public/data/provenance.json`.
