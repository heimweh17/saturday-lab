# Feature overlap, confidence and rest audit blueprint

This protocol is frozen before results are calculated. It tests whether the v6
strength stack gains useful independent information from first-down creation,
rushing EPA and yards per play, or merely produces excessive confidence from
correlated descriptions of the same performance.

## Baseline and candidates

Every target-season prediction uses only seasons before that target. The released
v6 broad bundle with ridge 1 is the baseline. The audit compares:

- compact: scoring strength, first-down rate, observed passer efficiency, venue
  and linear rest;
- stable pair: scoring strength, non-explosive EPA, first-down rate, passer,
  venue and linear rest;
- broad v6 under ridge 10 and 50;
- compact and broad variants that replace linear rest difference with three
  antisymmetric buckets: small (1-2 days), bye-sized (3-9) and long (10+);
- fixed probability-temperature multipliers 0.85, 0.90 and 0.95 applied to the
  complete broad logit. These directly test whether v6 is too confident.

The compact and stable-pair bundles use ridge 1 and 10. Team-strength and venue
coefficients stay nonnegative. Rest buckets remain signed. All models preserve
swap symmetry; all strength bundles retain a scalar ordering.

## Selection and confirmation

Pooled 2023-2024 log loss chooses one candidate. The 2025 season is then the
confirmation check. Partial 2026 results are diagnostic only.

Report accuracy, Brier score and log loss by season and pooled. Report favorite
calibration in fixed bands: 50-60, 60-70, 70-80, 80-85, 85-90, 90-95 and 95-100.
Also report the fraction of predictions above 90% and 95%, actual upset rates in
those groups, neutral-logit gap quantiles, and feature correlations on the
training design.

## Promotion gate

Production changes only if the selected candidate satisfies every condition:

1. pooled 2023-2025 log loss improves by at least 0.001;
2. pooled Brier score does not worsen;
3. 2025 confirmation log loss improves by at least 0.0005;
4. 2025 accuracy falls by no more than 0.5 percentage points;
5. no completed season regresses in log loss by more than 0.0015;
6. a 10,000-draw season-week block bootstrap favors the candidate at least 85%;
7. weighted absolute calibration error across the 90-95 and 95-100 favorite
   bands does not worsen.

If no candidate passes, v6 remains unchanged. The audit is retrospective and
does not turn 2025 into a pristine holdout; it only enforces a selection/
confirmation separation within the available inspected seasons.
