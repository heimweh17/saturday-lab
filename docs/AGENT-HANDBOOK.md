# Saturday Lab agent handbook

This document is the operating map for an agent making changes to Saturday Lab. Read it before editing. It explains which parts are presentation, which parts are published data, which outputs are frozen, and which checks protect the project from a small change affecting the whole archive.

## 1. Product and deployment

Saturday Lab is a personal, public college-football data publication. It covers FBS rankings, team reports, schedules, game centers, matchup simulation, rank trends, model documentation, and a permanent archive. The production site is a static Next.js export hosted from the `gh-pages` branch at `https://heimweh17.github.io/saturday-lab/`.

The main branch contains source code and published JSON. GitHub Pages does not execute a Next.js server. `npm run build:pages` sets `STATIC_EXPORT=1`, uses `/saturday-lab` as the base path, temporarily removes the optional API routes, exports the site to `out/`, and restores the API directory. `scripts/publish-pages.mjs` publishes the completed artifact to `gh-pages`.

The application is deliberately split into two clocks:

1. Mutable game facts refresh independently and frequently. Scores, status, kickoff, period scoring, box data, venue, broadcast, and current-season team schedule placement come from `public/data/live-2026.json`.
2. Rankings and forecasts are a formal weekly snapshot. They change only when the weekly model workflow succeeds and publishes a new static build.

Do not collapse these clocks. A Friday final may appear in the game center and move from a team's Upcoming section to Results while the ranking remains Monday's frozen board.

## 2. Repository map

| Path | Responsibility |
|---|---|
| `app/` | Next.js App Router pages and client UI. |
| `app/page.tsx`, `app/rankings-client.tsx` | Current ranking board and historical ranking snapshot UI. |
| `app/teams/` | Team directory, current team alias, and dated team-season pages. |
| `app/games/` | Scores/schedule index and permanent game centers. |
| `app/game-strip.tsx` | Current `UP NEXT` marquee board. |
| `app/matchup/`, `app/rank-trends/` | Hypothetical matchup lab and multi-team ranking charts. |
| `app/model/`, `app/methodology/`, `app/legal/` | Research explanation, methodology, sources, and legal context. |
| `components/ui/` | Shared primitive components. |
| `lib/model.ts` | Browser implementation of the published probability model. |
| `lib/production-config.json` | Frozen v6 selection, coefficients, validation summary, and rating configuration. |
| `lib/predict.ts` | Original score-based model kept for comparison/fallback contexts. |
| `lib/projected-score.ts` | Full-model expected-score layer that keeps score leader and win-probability leader consistent. |
| `lib/server-catalog.ts` | Build-time catalog for static team, game, season, and ranking routes. |
| `lib/routes.ts` | Canonical URL constructors and snapshot slugs. |
| `lib/game-navigation.ts` | Safe game-page origin query/session state and contextual Back behavior. |
| `lib/live-feed.ts` | Client fetch contract for the mutable current-game feed. |
| `analytics/` | Source acquisition, causal rating construction, model research, audits, weekly production, and tests. |
| `public/data/` | Published application data. These files are part of the product contract. |
| `.github/workflows/` | Frequent game refresh and formal weekly publication. |
| `scripts/` | Static build, verification, installation, and Pages publication. |
| `scripts/social/` | Deterministic weekly social-carousel selection, SVG templates and PNG rendering. |
| `docs/SOCIAL-GRAPHICS.md` | Social graphics data ownership, selection rules, CLI and manual Action workflow. |
| `docs/PRODUCT-BACKLOG.md` | Deferred product changes. Check before implementing a related request. |
| `analytics/*-RESULTS.md` | Research decisions and evidence. Read the relevant report before changing the model. |

Legacy directories such as `.sites-runtime`, `.vinext`, and some starter infrastructure are not the production path. The active site runs native Next.js 16.

## 3. URL contract

URLs are product behavior, not incidental router state.

### Rankings

- `/` and `/rankings/` are aliases for the current season's latest published snapshot.
- `/rankings/2025/` is the final or latest published snapshot for that season.
- `/rankings/2025/week-5/` is an exact frozen weekly board.
- Postseason snapshots use `postseason-N` rather than an ambiguous integer.

### Teams

- `/teams/florida-gators/` is the current-season alias.
- `/teams/florida-gators/2025/` is the permanent team-season page.
- Team-season-week URLs are intentionally deferred. The current route helpers keep that extension possible.

### Games

- `/games/2026/florida-gators-at-tennessee-volunteers-<game-id>/` is a permanent game identity.
- The ESPN game ID is the stable unique key. Do not create a second identity for the same game.
- Links into a game may add `from` and `fromLabel` query parameters. `lib/game-navigation.ts` validates them as internal paths and records a short-lived session marker. The Back button uses real history only when the marker proves the user actually arrived from that page; otherwise it routes to the exact saved path.
- A game opened from `/teams/florida-gators/2025/` or `/rankings/2025/week-5/` must return to that exact historical context.

All internal team links on historical pages should use the dated season route. Current-season UI should prefer the short alias. Use helpers from `lib/routes.ts`; do not hand-build slugs in components.

## 4. Published data contracts

`public/data/manifest.json` is the season index. At the time of this handbook it covers 2018–2026 and identifies 2026 as `latestSeason`. Code should read that field instead of scattering a new hard-coded year.

Important files:

| File | Meaning and mutation policy |
|---|---|
| `manifest.json` | Available seasons, latest season, source audit, high-level config. Weekly/research publication only. |
| `<season>.json` | Weekly snapshots, teams, completed games, frozen historical predictions, production model payload. Historical seasons are immutable. |
| `fixtures.json` | Full current-season published schedule and coverage audit. Refreshed during the weekly pipeline. |
| `live-2026.json` | Mutable current-game feed. Refreshed hourly without a full site build. |
| `box-<season>.json` | Team box-score archive. Historical files are fixed; current year updates weekly. |
| `periods-<season>.json` | Validated scoring by period. Current completed live periods are archived weekly. |
| `model.json` | Research report, temporal validation, FPI diagnostics, predictions, and provenance. |
| `report.json` | Older scoring-model report still used by portions of the UI. |
| `score-layer.json` | Frozen full-model expected-score calibration. It changes score display, not win probabilities. |
| `research-stage*.json` | Published audits and rejected/retained experiments. Never treat a candidate as production just because it exists here. |
| `provenance.json`, `linescore-sources.json` | Source URLs, checksums, and period-score provenance. |

### Snapshot convention

Within `<season>.json`, normal numbered keys represent pregames snapshots. Key `99` means the latest/final published snapshot for that season. `weeks` includes `99`. The server catalog converts numbered keys into `week-N` or `postseason-N` routes.

### Frozen predictions

Historical `predictions` are archives of what the model knew before kickoff. `analytics/weekly_refresh.py` carries an existing probability, cutoff, and model version forward instead of recalculating it with later information. `analytics/live_feed.py` freezes a current game's pregame record when it starts. Do not recompute old pregame probabilities during a UI change or weekly update.

### Missingness

Missing values are not zero. Rate calculations preserve missing denominators. FCS games can appear in schedules and results but are excluded from FBS probability fits. If a game or team is outside model coverage, show that honestly instead of fabricating a forecast.

## 5. Production model v6

The published win model is a causal, time-ordered logistic model. A game's inputs use only team state available before that game. The conceptual form is:

```text
logit(P(A wins)) = coefficient · (state_A - state_B, venue, rest difference)
```

For v6, nonzero fitted terms are:

- opponent-adjusted scoring strength;
- opponent-adjusted first-down creation;
- opponent-adjusted rushing EPA;
- opponent-adjusted yards per play;
- prior observed-passer efficiency;
- home field;
- rest difference, with a fitted effect very close to zero.

The rating state retains 65% offseason carry, uses a four-signed-class recruiting prior, shrinkage/ridge controls, and weekly game-state updates. Recruiting is a preseason proxy. It is not a transfer-portal roster, depth chart, redshirt model, or injury model.

The model deliberately excludes unverifiable future starters, complete transfer-adjusted rosters, injuries, weather, betting lines, coaching changes, and garbage-time corrections. A UI must not imply those inputs are present.

`lib/production-config.json` is the production truth for coefficients. `analytics/weekly_refresh.py` applies the frozen specification; the weekly workflow does not refit or select a new model. Model changes require a separately designed time-ordered audit, comparison with production, calibration checks, a written result, and an explicit promotion decision.

### Existing evidence

- V6 was selected on pooled prior-year log loss with nested temporal selection.
- FPI is a diagnostic comparison, not a training target.
- `analytics/HOME-FIELD-AUDIT-RESULTS.md` retained the fitted home term after equal-strength and rolling validation.
- `analytics/FEATURE-OVERLAP-AUDIT-RESULTS.md` retained the broad feature bundle after compact bundles, stronger ridge, confidence shrinkage, and categorical rest alternatives lost.
- `analytics/DURABILITY-REVIEW.md` documents rejected preseason/returning-production alternatives.
- `analytics/FULL-SCORE-LAYER.md` documents the expected-score layer.

Read these reports before proposing a model edit. Do not infer importance by comparing raw coefficient magnitudes because inputs have different scales.

### Expected scores

The score layer is separate from the probability model but anchored to it. A positive robust mapping converts the v6 probability logit into expected margin; an opponent-adjusted scoring total estimates pace; the two team scores are derived from margin and total. The displayed score leader must always match the probability leader. Decimal scores are expectations, not literal predicted final scores.

## 6. Current-game refresh

`.github/workflows/live-game-refresh.yml` has two independent triggers:

- QStash calls `workflow_dispatch` in the `America/New_York` timezone and supplies `trigger=qstash`: every three hours Monday through Thursday, hourly Friday and Sunday, and every 15 minutes Saturday.
- GitHub's native schedule is retained as a slower best-effort fallback: every four hours Monday through Thursday, every two hours Friday and Sunday, and every 30 minutes Saturday (GitHub cron is UTC).

The QStash credential is a fine-grained GitHub token with no expiration, limited to `heimweh17/saturday-lab`, with `Actions: read and write` plus required metadata read access. The secret lives only in QStash, is forwarded as the GitHub Authorization header, and is redacted in the QStash console. Never commit or print it. If it must be rotated, pause the schedule, revoke the old token, create the replacement with the same minimal scope, update the redacted header, resume, manually trigger once, and verify a GitHub run titled `Refresh current games · qstash`.

The workflow:

1. checks out `main`;
2. runs `analytics/live_feed.py`, retrying the entire refresh up to three times;
3. commits only when semantic game data changed;
4. pushes only `public/data/live-2026.json`.

`lib/live-feed.ts` lets the production browser read the raw file from `main` with a five-minute cache bucket and fall back to the copy bundled in the last Pages artifact. This is how current facts update without regenerating more than 9,000 pages. The Scores page gets the most recent successful check time from GitHub's public Actions API; that timestamp advances even when the semantic feed is unchanged and no commit is created.

The live feed also drives current team-page schedule placement. A completed game moves from Upcoming to Results as soon as the feed marks it final; the team ranking and season aggregates still remain frozen until Monday.

## 7. Weekly publication and the UP NEXT board

`.github/workflows/weekly-model-refresh.yml` runs Monday at 14:30 UTC and is also manually dispatchable. It:

1. downloads operational sources with `analytics/production_sources.py`;
2. runs `analytics/weekly_refresh.py` with the frozen v6 configuration;
3. refreshes the current schedule through `analytics/fixtures.py`;
4. refreshes the live feed;
5. runs all Python tests, shared TypeScript/Python forecast checks, lint, and the complete static export;
6. commits the current data files if they changed;
7. publishes the static artifact to `gh-pages`.

The shared publication concurrency group prevents a weekly write from racing a live-feed write. Before the expensive job begins, a same-day guard skips a second formal publication unless a manual operator deliberately selects the `force` input. The independent QStash schedules target only `live-game-refresh.yml`; they never invoke the weekly workflow.

`social-graphics.yml` is a read-only, manually dispatched presentation workflow. It can render either the pregame Weekly Preview or the postgame Monday Recap from already published snapshots, frozen pregame forecasts, final scores and box data. It never commits, deploys, refits the model or creates a new weekly snapshot. See `docs/SOCIAL-GRAPHICS.md`.

`preview-current-rankings.yml` is an intentionally nonpublishing research path linked by the current rankings page. It calculates with the same frozen v6 pipeline, shows the Top 30 in the Actions summary, retains a complete JSON artifact for one day, and has only `contents: read`. Do not add commit, Pages publication or dated-snapshot writes to this workflow.

The homepage `UP NEXT` board is computed in `app/game-strip.tsx` from the refreshed `fixtures.json` plus the latest `99` snapshot. It finds the earliest remaining scheduled FBS week, scores games by 60% team quality and 40% projected closeness, applies the published eligibility rule, and shows up to 10 games. Therefore it advances automatically after the Monday fixture/model update; it is not a hard-coded Week 4 list. Exact historical ranking snapshot pages omit this current-week board so their context stays frozen.

The frequent feed and weekly workflow share one concurrency group so they cannot push competing commits. Both must remain idempotent: game ID is the unique key, and no-change refreshes exit without a commit.

## 8. UI and navigation boundaries

The product is a sports data site first. Rankings, teams, scores, and game information belong in the main navigation. Model explanation belongs in the Model/Methodology routes and should not dominate ordinary reader pages.

Important interaction rules:

- Team names consistently open team pages.
- Schedule/result rows open the permanent game page; clicking the opponent name opens the opponent team page.
- Current-season team links use the short URL; historical contexts use the dated team-season URL.
- Matchup Lab is hypothetical. Real scheduled games use permanent game pages.
- Probabilities display one decimal place where the data supports it. Do not silently round 49.6% to 50%.
- Technical notes are useful when they explain a real method, definition, source, or limitation. Remove generic filler that merely restates a heading.
- Desktop and 390px mobile are both supported. Large charts must remain usable with zoom/reset controls and readable hover details.

## 9. Safe change workflow

Before editing:

1. Run `git status --short --branch` and inspect attached worktrees. Do not overwrite unrelated uncommitted work.
2. Read this handbook, `README.md`, and the focused source file or research report.
3. Search with `rg` for every caller of a changed prop, route helper, or data field.
4. For Next.js behavior, read the relevant local guide under `node_modules/next/dist/docs/`; this repository uses Next.js 16 and may differ from older assumptions.

For a UI-only change, do not regenerate research data. For a data-pipeline change, state which published files should change. For a model experiment, keep candidates out of production until the promotion evidence is written and reviewed.

Avoid these high-risk shortcuts:

- editing generated JSON by hand;
- replacing a frozen historical probability with today's rating;
- hard-coding `2026` in new generic route code when `manifest.latestSeason` is available;
- using external team names to make independent slugs when canonical route helpers exist;
- rebuilding all static pages for an hourly score update;
- changing coefficients during a front-end task;
- pushing `out/`, `.next/`, operational caches, or credentials to `main`;
- publishing only selected historical HTML from a new build, because hashed framework assets may no longer match.

## 10. Verification matrix

Use the smallest meaningful checks first, then the complete publication checks before pushing a cross-cutting change.

```powershell
npm run lint
npm run test:social
node scripts/check-model.mjs
python -m unittest discover -s analytics -p 'test*.py' -v
npm run build:pages
```

Expected non-blocking lint state: the shared logo component currently has one `@next/next/no-img-element` warning. New warnings should be investigated.

`scripts/check-model.mjs` reproduces all published Python forecasts with the TypeScript model, checks complementary probabilities, and validates the exact remaining-win distribution.

The complete Pages build is intentionally large. At the time this handbook was written it generated 9,268 static pages: the game archive, current team aliases, 1,190 dated team seasons, nine season ranking pages, and 135 exact ranking snapshots. A successful route listing is evidence that every static parameter resolved.

After a route change, inspect representative files in `out/`:

```text
out/rankings/2025/index.html
out/rankings/2025/week-5/index.html
out/teams/florida-gators/2025/index.html
out/games/2026/<slug>/index.html
```

After an automation change, verify the actual GitHub Actions run, not only the scheduler's success toast. A QStash dispatch must appear as `workflow_dispatch`, use the intended head SHA, and complete successfully.

## 11. Common task map

| Request | Start here | Also inspect |
|---|---|---|
| Change ranking table or homepage | `app/rankings-client.tsx` | `app/game-strip.tsx`, `app/strength-map.tsx`, `app/snapshot-pulse.tsx` |
| Change a team report | `app/scouting.tsx` | `app/teams/[team]/team-page-client.tsx`, `app/forecast.tsx` |
| Change completed game details | `app/games/[season]/[game]/game-page-client.tsx` | box/period JSON contracts, `lib/live-feed.ts` |
| Add or change permanent routes | `lib/routes.ts`, `lib/server-catalog.ts` | route `page.tsx`, `app/sitemap.ts`, navigation origin handling |
| Change current score refresh | `analytics/live_feed.py` | live workflow, `lib/live-feed.ts`, `analytics/test_live_feed.py` |
| Change Monday publication | `analytics/weekly_refresh.py` | weekly workflow, fixtures, full verification suite |
| Research a model idea | relevant audit blueprint/result | causal state construction, nested temporal selection, calibration slices |
| Change expected scores | `lib/projected-score.ts`, `analytics/full_score_layer.py` | score-layer tests and report |
| Change deployment | `scripts/build-pages.mjs`, `scripts/publish-pages.mjs` | `next.config.ts`, both workflows, GitHub Pages base path |
| Change social graphics | `docs/SOCIAL-GRAPHICS.md`, `scripts/social/` | published data contracts, `social-graphics.yml`, visual contact sheet |

## 12. Current known boundaries

- GitHub scheduled events are not reliable enough to be the sole frequent clock; QStash is the primary trigger and GitHub cron is fallback.
- Weekly builds still regenerate the complete archive. The stable routes make future build reuse possible, but copying old HTML alone is unsafe until framework asset versioning is solved.
- `UP NEXT` advances on the weekly fixture refresh, not minute by minute.
- The current-season live feed can change game placement and facts but not weekly ranking totals.
- Team-season-week permalinks are reserved for a later phase. Do not add them casually without extending return navigation, sitemap generation, and static-parameter tests together.
- Weather, injuries, complete transfer rosters, betting lines, and verified future starters are outside current data coverage.

When uncertain, preserve causality, archived predictions, stable game IDs, route permanence, and the split between live facts and weekly opinion. Those are the core invariants of the project.
