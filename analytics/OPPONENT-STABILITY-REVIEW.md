# Opponent-adjusted stability follow-up

The frozen pregame-feature study found a promising raw success-rate signal. Before any production
change, this follow-up tests the mechanism most likely to create a false gain: schedule strength.
The design is fixed before inspecting these results.

Use the already hash-pinned advanced team game logs. For each completed game, build separate
opponent-adjusted ratings for non-explosive EPA, first-down-created rate, passing EPA, rushing
EPA, yards per play and explosive-play rate with the production rating's 0.65 year carry,
lambda/2 unit shrinkage and 0.97 weekly decay. The target week's game is never in its snapshot.
No recruiting shift is applied to these unit ratings.

Hold the v5 scoring configuration and observed-passer construction fixed. Test baseline;
non-explosive EPA; first-down rate; the stable pair; pass/rush EPA; yards per play; explosive
rate; and a broad bundle. Each bundle uses ridge 1, 10 or 50 and the same previous-three-year
rolling selection as the preceding stage. Directional coefficients are nonnegative; rest is
signed. There are no availability or school-specific terms.

Apply the same promotion gate: at least 0.002 lower pooled 2024-2025 log loss than locked v5, no
more than 0.002 worse in either complete season, no more than 0.5 percentage-point pooled accuracy
loss, and at least 90% week-block bootstrap probability of lower log loss. Report 2023 and partial
2026, but neither can override that gate. If the opponent-adjusted signal fails, retain v5.
