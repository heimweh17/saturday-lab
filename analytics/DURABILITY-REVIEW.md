# Durability and preseason-information review

The published v6 model is frozen before this study. ESPN's public FPI methodology motivates the
hypotheses—prior performance, returning starters, recruiting and coaching tenure form a preseason
rating whose influence falls as games arrive—but ESPN rankings are never a training target.

## Inputs and leakage exclusions

Use the hash-pinned v6 game, advanced-stat, recruiting and observed-passer inputs plus public
`cfb_matchup_line` preseason side inputs for 2019-2026. Only `ovr_rtprod`, `off_rtprod`,
`def_rtprod`, `hc_tenure`, `oc_cont` and `dc_cont` may be read from the new files. Explicitly ban
betting lines, final scores, weather, realized-season QB identity/returning-QB fields, opponent-Elo
rolls and the matchup feature block. Standardize preseason inputs within the known FBS field;
missing values receive the season mean. Record SHA-256 hashes.

## Frozen hypotheses

Keep the v6 scoring prior, recruiting definition, observed-passer construction and scalar neutral
strength. Test whether opponent-adjusted efficiency ratings need less year-to-year persistence than
scoring. The nine prespecified unit configurations are v6 (carry .65, lambda 1, decay .97), carry
0/.25/.45, lambda .5/2/4, and decay .94/1.00, changing one axis at a time.

For each unit configuration test five component bundles: v6 broad, first-down only, yards only,
stable first-down plus non-explosive EPA, and pass/rush EPA. Test these preseason structures:

1. v6 combined scoring state;
2. separate preseason scoring strength and in-season change;
3. that split with preseason half-life 4, 8 or 12 completed weeks;
4. v6 scoring plus returning production with half-life 4 or 8;
5. v6 scoring plus returning production and staff continuity with half-life 8;
6. split scoring plus returning production with half-life 8.

Use ridge penalties 1, 10 and 50. Directional strength, returning-production and continuity
coefficients are nonnegative; rest is signed. No school-specific rule is allowed.

## Evaluation and decision

For target seasons 2023-2026, each candidate's inner predictions train only on prior seasons.
Choose pooled previous-three-year log loss, then refit through targetYear-1. Compare on identical
games with frozen v6, v5 and the original benchmark.

Promotion requires at least .0015 lower pooled 2023-2025 log loss than v6, no complete season more
than .003 worse, pooled accuracy no more than .5 percentage points worse, and at least 90% chance
of lower log loss in a season-week block bootstrap. Partial 2026 and current FPI rank agreement are
diagnostic only. Failure keeps v6 online and publishes only the research result.
