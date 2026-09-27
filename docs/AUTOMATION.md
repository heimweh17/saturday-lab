# Automated season operations

Saturday Lab separates changing game facts from the formal model publication cycle.

## Current-game feed

`.github/workflows/live-game-refresh.yml` accepts both GitHub's best-effort schedule and authenticated `workflow_dispatch` calls from the independent scheduler. The external schedule is the primary clock: Monday through Thursday every three hours, Friday and Sunday hourly, and Saturday every 15 minutes. GitHub provides a slower fallback at four hours Monday through Thursday, two hours Friday and Sunday, and 30 minutes Saturday. Dispatch calls label themselves through the `trigger` input so the Actions log shows which clock started each run. It queries every current FBS team schedule, deduplicates events by ESPN game ID, and requests summaries only for active, newly final or nearby games that still need detail. A failed full refresh is retried twice with increasing delays before publication is stopped. The output is `public/data/live-2026.json`.

The browser reads that file directly from the `main` branch with a five-minute cache window and falls back to the copy bundled into the latest Pages artifact. Scores, status, kickoff, period scoring and available box-score details can therefore change without rebuilding the historical static archive. Current-season team reports use the same feed, so a final moves from Upcoming Games to Results promptly while rankings and season summaries remain on the weekly snapshot. A semantic comparison excludes the retrieval timestamp; an unchanged feed produces no commit. The Scores page separately reads the latest successful workflow run time from GitHub's public Actions API, so its freshness label advances after a successful check even when the feed itself is unchanged.

The feed also carries the current weekly pregame probability. A scheduled game receives the current formal snapshot. Once it starts, that record is frozen and later refreshes preserve it. Historical completed games keep their archived prediction. The game ID is the stable unique key, so a retry replaces the same record rather than ingesting another copy.

## Formal weekly snapshot

`.github/workflows/weekly-model-refresh.yml` runs Monday at 14:30 UTC and can also be started manually. It downloads a separate rolling operational source cache, rebuilds only the current season with the frozen v6 feature set and coefficients, updates current box and period archives, refreshes the future schedule, runs model/application checks, creates a complete static export and publishes `gh-pages`.

The workflow-level publication lock serializes it with live-feed writes. A same-day guard then skips a second formal weekly run after one has already published, so a scheduled run and an accidental manual run cannot create redundant formal releases. Manual dispatch exposes an explicit `force` input for a deliberate corrected republication.

`.github/workflows/preview-current-rankings.yml` is the separate research button behind **Unofficial preview** on the current rankings page. It runs the same frozen v6 source and ranking calculation in an ephemeral Actions workspace, writes the Top 30 to the run summary, and keeps a full JSON artifact for one day. It has read-only repository permission and never commits, updates a dated snapshot, rebuilds Pages or changes the live site.

Research source files and their checksums remain separate. The weekly job follows current upstream releases but cannot overwrite a frozen research manifest or refit/select a model. If a just-finished game has conflicting score and advanced-stat releases, the job quarantines that game from the formal model snapshot; the live feed can still show its final score, and a later weekly run includes it after the upstream files agree.

Rankings and future probabilities therefore identify one stable weekly cutoff. A Friday final can appear quickly in Scores and its game center while the ranking remains Monday's published snapshot. It enters the rating at the next successful formal refresh.

Historical team-season and ranking-snapshot URLs are immutable views of the committed season JSON. The current build still performs one complete Next.js static export, even though those historical inputs do not change. Reusing frozen HTML safely is a separate build optimization: old pages reference hashed framework assets, so copying only their HTML into a new artifact could leave broken script references. The route structure keeps that optimization possible without coupling it to the weekly model update.

## Failure behavior

Both workflows share one concurrency group, so they do not push competing commits. A failed fetch, incomplete team-schedule coverage, model assertion, test, lint or build stops publication. Generated operational caches are ignored by Git. The weekly data commit occurs only after verification, and the Pages artifact is pushed only after a successful static build.

The external scheduler calls GitHub's workflow-dispatch endpoint with a fine-grained token restricted to this repository and `Actions: write`. The workflow's own short-lived `GITHUB_TOKEN`, restricted to `contents: write`, remains the only credential that can publish game data. The independent schedule and its secret live outside the repository; no credential is committed here.
