# Home-field audit blueprint

This document freezes the test before its results are calculated. The question is
whether the v6 home-field coefficient is too large, not whether a smaller number
looks more comfortable.

## Model under review

The audit reconstructs the released v6 broad model with its published rating
configuration, feature bundle, ridge penalty, positive-coefficient constraints,
and week-forward snapshots. A target-season fit may use only prior seasons from
2019 onward. Reproducing the saved v6 probabilities is a required integrity
check.

The 3-point value in the scoring-rating layer removes venue from observed score
margins while estimating team strength. It is not added to the game logit. The
explicit home coefficient is therefore the final model's direct venue term.

## Variants

The released model fits home field freely. It is compared with otherwise
identical models whose raw-logit home coefficient is fixed at 0.15, 0.20, 0.25,
or 0.30. All other coefficients are refit for every target season with the same
ridge objective. The fixed coefficient is an offset during optimization, so it
cannot be changed indirectly by feature scaling.

The fixed candidate with the lowest pooled 2023-2024 log loss is selected before
2025 is examined as confirmation. Partial 2026 results are reported only as a
diagnostic.

## Measurements

For each season, report accuracy, Brier score, and log loss. Also report:

- the freely fitted coefficient and its equal-team home win probability;
- non-neutral games whose released model, with venue removed, places the home
  side between 40% and 60%;
- actual and predicted home win rates in that near-even slice;
- coefficients from a score-only, baseline, stable-pair, and broad feature set,
  to test whether adding efficiency inputs destabilizes the venue estimate;
- a 10,000-draw season-week block bootstrap of the candidate-minus-released log
  loss on completed 2023-2025 seasons.

The near-even slice is defined once from the released free model so every variant
is measured on the same games. Rest remains in the neutralized probability;
only venue is removed.

## Promotion rule

Changing production requires all of the following:

1. pooled 2023-2025 log loss improves by at least 0.0005;
2. pooled Brier score does not worsen;
3. no completed season's log loss worsens by more than 0.001;
4. bootstrap probability of lower log loss is at least 80%;
5. absolute calibration error in the pooled near-even slice improves;
6. 2025 confirmation log loss improves and accuracy falls by no more than 0.5
   percentage points.

If the gate fails, v6 stays unchanged. This is a retrospective audit of seasons
already inspected during model development, not a pristine holdout claim.
