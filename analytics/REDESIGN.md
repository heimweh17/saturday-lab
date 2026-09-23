# Model redesign blueprint

Objective: improve forward prediction across the FBS field; ESPN FPI is an external diagnostic, not a target label. No school-specific adjustments.

1. Audit timestamps, membership, missing values and game joins before modeling. Reject FPI records updated after a prediction cutoff even if their week label looks historical. Report coverage of valid records.
2. Reference ESPN's public description: opponent-adjusted unit efficiency, controlled blowout influence, multiyear history and personnel-aware preseason estimates. ESPN's proprietary coefficients are unavailable; this project does not replicate FPI.
3. Compare scoring-network ratings, capped margins, multiple prior strengths and multi-season carry, EPA offense/defense and special teams, and personnel/talent inputs when provenance permits. Missing data remain explicit. Do not label aggregate EPA as garbage-time filtered unless the source supports it.
4. Mathematical core: minimize sum w_g (observed unit performance - league mean - offense_i + defense_j)^2 + lambda sum (unit rating - preseason prior)^2. Margin network uses r_i-r_j+home advantage. Test robust/capped outcomes separately. Fit win probabilities using antisymmetric pregame rating differences, with regularization and training-only scaling.
5. Freeze candidate definitions before evaluation. Select by earlier-year log loss; evaluate annual rolling origin without random splits. Retain original and v3 benchmarks, inspect Brier, accuracy, calibration, early weeks, conference-crossing games and strength strata. Already-inspected seasons remain retrospective, never pristine holdouts.
6. Compare the whole current ranking with dated FPI: rank correlation, mean rank difference, largest disagreements and conferences. Use only correctly dated historical FPI for historical prediction comparisons; report missing coverage.
7. Publish one validated model only if justified. Export all research evidence, clear limitations, equations, data sources and cross-language verified forecasts. Preserve reproducibility and the old baseline.
