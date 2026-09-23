# Prior-only follow-up protocol
Stage one improved pooled probability loss modestly but its explicit calendar recruiting decay can still offset improving performance. Before running this stage, replace the direct recruiting bonus with a preseason prior inside the opponent-adjusted scoring fit. No team-specific or rank-target objective is introduced.

Net preseason scoring prior = carry * previous final net score rating + gamma * (centered recruiting composite / 1000 + centered blue-chip share). Half enters offense and half defense. Gamma = 0, 6 or 12 points. The current year's observed games update the prior through the same ridge objective. There is no explicit week-by-week talent subtraction.

72 rating designs: carry .35/.65 x prior penalty 1/2/4 x raw or bounded pregame margin surprise x uniform or pregame mismatch weights x gamma 0/6/12. Four feature bundles (score, score+Elo, score+EPA+special teams, score+EPA+special teams+Elo) x two logistic penalties = 576 candidates. Coefficients remain nonnegative for strength and venue, with unrestricted rest.

Use the identical nested, expanding-year validation and minimum earlier-year log loss rule. Evaluate against original/v3/v4, the first experimental stage, timestamp-valid FPI, early/late and competitive/mismatch slices. Document every result, including failures. Already seen seasons are not new holdouts. Do not keep expanding the grid in response to a named team's resulting rank.
