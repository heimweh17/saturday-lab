# Automated season operations

Saturday Lab separates changing game facts from the formal model publication cycle.

## Current-game feed

`.github/workflows/live-game-refresh.yml` runs every two hours. It queries every current FBS team schedule, deduplicates events by ESPN game ID, and requests summaries only for active, newly final or nearby games that still need detail. The output is `public/data/live-2026.json`.

The browser reads that file directly from the `main` branch with a five-minute cache window and falls back to the copy bundled into the latest Pages artifact. Scores, status, kickoff, period scoring and available box-score details can therefore change without rebuilding the historical static archive. A semantic comparison excludes the retrieval timestamp; an unchanged feed produces no commit.

The feed also carries the current weekly pregame probability. A scheduled game receives the current formal snapshot. Once it starts, that record is frozen and later refreshes preserve it. Historical completed games keep their archived prediction. The game ID is the stable unique key, so a retry replaces the same record rather than ingesting another copy.

## Formal weekly snapshot

`.github/workflows/weekly-model-refresh.yml` runs Monday at 14:30 UTC and can also be started manually. It downloads a separate rolling operational source cache, rebuilds only the current season with the frozen v6 feature set and coefficients, updates current box and period archives, refreshes the future schedule, runs model/application checks, creates a complete static export and publishes `gh-pages`.

Research source files and their checksums remain separate. The weekly job follows current upstream releases but cannot overwrite a frozen research manifest or refit/select a model. If a just-finished game has conflicting score and advanced-stat releases, the job quarantines that game from the formal model snapshot; the live feed can still show its final score, and a later weekly run includes it after the upstream files agree.

Rankings and future probabilities therefore identify one stable weekly cutoff. A Friday final can appear quickly in Scores and its game center while the ranking remains Monday's published snapshot. It enters the rating at the next successful formal refresh.

## Failure behavior

Both workflows share one concurrency group, so they do not push competing commits. A failed fetch, incomplete team-schedule coverage, model assertion, test, lint or build stops publication. Generated operational caches are ignored by Git. The weekly data commit occurs only after verification, and the Pages artifact is pushed only after a successful static build.
