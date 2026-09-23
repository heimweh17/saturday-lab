# Ranking review, September 23

This revision investigates all FBS teams, not a target ranking for Florida or Houston.

## Diagnosis before experimentation

Florida's 2026 scoring power increased from 7.969 to 8.957 after beating Auburn 44-39 away. Net EPA increased from .1325 to .1430. Holding the rest of the field fixed, its neutral win index rises from .80914 to .81564. With its old sample count it would be .82063. Updating the whole field instead gives .80497 and rank 16 -> 17. Thus opponent adjustment exists; the drop is not simply a penalty for the Auburn win. A pair-dependent recruiting decay and changes elsewhere obscure the positive game evidence.

V4 multiplies the talent difference by exp(-min(samples_A, samples_B)/4). A team's effective talent contribution therefore depends on the opponent's sample count. This cannot generally be expressed as one scalar team strength. FCS games do not increment those counts. The redesign will eliminate that interaction, not manually reward named teams.

## Frozen experiment design

- 36 rating configurations: carryover 0/.35/.65; prior penalty 1/4; raw, 28-point margin cap, or bounded pregame margin surprise; uniform or pregame mismatch weights.
- Both scoring and EPA explicitly fit opponent offense/defense. Joint weighted ridge uses only earlier weeks. Mismatch weight is max(.25, 4p(1-p)) from that configuration's pregame scoring expectation, applied symmetrically to the game. A weak opponent is already adjusted for by the fit; extra weighting must earn its place in validation.
- Surprise compression changes the margin to expected_margin + 28*tanh((actual_margin-expected_margin)/28), preserving total points. Unlike capping every margin, it distinguishes an expected blowout from an unexpected one. It uses the pregame expectation and never refits it using that game's result.
- Unit priors use the same carryover and half the scoring penalty. EPA/play and special teams EPA/game are separate units. Missing pairs remain omitted. No claim of verified garbage-time removal.
- Six feature bundles: score; score+Elo; score+EPA+special teams; score+EPA+special teams+Elo; all with constant recruiting; all with recruiting decaying by the common season week exp(-completed_weeks/6), independent of the opponent or number of games played.
- Two regression penalties 1/10: 432 candidates total. Every team-strength coefficient and home advantage is nonnegative; rest is unconstrained. Logistic fits have no intercept. All inputs are differences of team-local components, yielding a single transitive neutral-field strength, with venue/rest added only for games.
- For each 2023-2026 target season select by pooled log loss over the previous three seasons, with every inner year trained only on previous years. Refit through targetYear-1. Do not select using current ranks, FPI agreement, Florida/Houston outcomes, or outer-year results.
- Compare v1, v3 and v4 on identical games: accuracy, Brier, log loss, calibration, early/late weeks, cross-conference and pregame mismatches. Paired week bootstrap quantifies uncertainty. Inspect all teams' win/rank changes. Use timestamp-valid FPI as a separate benchmark.
- Already inspected historical seasons and revised upstream EPA are retrospective evidence, not an untouched holdout. If this search does not justify a replacement, retain the deployed model and publish the result honestly.

ESPN references: https://www.espn.com/blog/statsinfo/post/_/id/122612/an-inside-look-at-college-fpi and https://espnpressroom.com/feature/heres-playbook-stats-info-explains-football-power-index-terminology/ . FPI is a predictive power measure, distinct from strength of record. Its proprietary formula is not available for reproduction here.
