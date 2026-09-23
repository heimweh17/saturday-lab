# First-model frozen forecast page

A separate, unlinked static page at /first-model/2026-09-23/. Production routes and data remain untouched.

## Design plan
Paper white #ffffff, cool background #edf2f5, navy ink #173149, field blue #1768ac, result green #226b50, muted red #9b4545. Segoe UI / Microsoft YaHei for readable bilingual text, Georgia for the short English notebook title. Left aligned, broad schedule ledger, tabular numeric columns. No decorative dashboard cards. A dated blue spine emphasizes this is a frozen forecast record.

[Notebook title / frozen date / downloads]
[Prediction cutoff and scope]
[Team search / week / result filter]
[Scored games / accuracy / Brier / log loss]
[Date | Away at home | Pick | Win probability | Result]
[Expandable method and source notes]

Review: a generic KPI-card hero would obscure the actual purpose. Use the dated ledger as the main visual element, with small inline summaries and a visible distinction between frozen predictions and locally entered results. Mobile retains a readable horizontal table inside its own scroll container.

## Analytics and evaluation
Recompute the original locked scoring model from hash-verified historical CSVs: shrinkage 2, home +2, decay 1, carry .65, logistic scale 8, Elo blend zero. Verify all 2023–26 original benchmark probabilities before export. Use the current completed-game cutoff and only scheduled fixtures after sealing time. Exclude FCS probabilities and unannounced future matchups. Preserve full precision probabilities and rating states. Publish JSON + CSV, source hashes and timestamp. Refuse to overwrite a sealed forecast.

Keep forecast fixed for the season; this tests today's long-horizon forecasts, not weekly refitted performance. Results are manually entered locally with a final-score validation form, deletable individually and exportable/importable as a backup. Only modeled, non-tied final results enter accuracy/Brier/log loss. Summary follows active filters. No server storage or automatic result refresh is implied.
