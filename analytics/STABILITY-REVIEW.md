# Stability review blueprint

This study freezes the published v5 model before inspecting any new result. It asks whether
strictly pregame play-level summaries add repeatable predictive information. It is a
retrospective research stage, not a pristine holdout, and it never targets a named team's rank.

## New source and leakage rule

Use the public `cfb_matchup_features` parquet files from the cfbfastR data repository for
2019-2026. Each row is a team snapshot computed strictly before that game. Verify every fetched
file against a recorded SHA-256 hash. Exclude realized-season QB identity, roster, coaching,
betting-line, final-score and opponent-Elo fields. Join only by game ID and team ID, then verify
the row date, week and team identities against the already frozen game file.

## Prespecified hypotheses

The locked v5 scalar scoring rating is the baseline team signal. Test whether the following
pregame offense-minus-defense matchup summaries improve it: EPA, WEPA, success rate, early-down
success, pass EPA, rush EPA, pass success, rush success, scoring-opportunity over expected,
points per scoring opportunity, starting field position, third-down tendency, and pace.

Feature bundles are fixed before results: baseline; balanced EPA; stable efficiency; pass/rush;
finishing/field position; situational; broad; and each single family added to baseline. Missing
first-game values are filled only with the training-season median plus an availability indicator.
All directional team-strength coefficients are constrained nonnegative. Rest, evidence
availability, pace and third-down tendency may be signed. Ridge penalties are 1, 10 and 50. No
school-specific adjustment is allowed.

## Rolling evaluation

For each target season 2023-2026, fit each candidate separately for every prior inner season,
using only games from 2019 through the year before that inner season. Select on pooled log loss
from the preceding three seasons, then refit through the target season minus one. Report log loss,
Brier score and winner accuracy on the untouched target-year rows within this stage. Compare on
the exact same games with locked v5, v4 and v1 probabilities.

## Promotion gate

Do not replace v5 unless the selected design beats locked v5 in pooled 2024-2025 log loss by at
least 0.002, is no worse by more than 0.002 in either complete season, does not reduce pooled
winner accuracy by more than 0.5 percentage points, and the improvement survives a week-block
bootstrap with at least 90% probability of lower log loss. The partial 2026 season is reported but
cannot authorize promotion. A failed gate leaves the production model and live site unchanged.
