# Full-model expected-score layer

The published v6 probability remains unchanged. A positive Huber-fitted scale converts its frozen pregame logit into expected margin, so the score leader always agrees with the probability leader. A linear calibration of the existing opponent-adjusted scoring total supplies game total; the two expected team scores are `(total ± margin) / 2`.

Selection used 2023–2024 rolling out-of-sample results; 2025 was the final untouched season test. The selected layer uses `huber` margin calibration and `linear` total calibration. Production parameters use 6,024 completed games through 2025.

| Season | Margin MAE baseline → layer | Total MAE baseline → layer | Team-score MAE baseline → layer |
|---|---:|---:|---:|
| 2023 | 12.595 → 12.621 | 13.223 → 13.134 | 9.209 → 9.251 |
| 2024 | 12.866 → 12.627 | 13.273 → 12.935 | 9.243 → 9.114 |
| 2025 | 12.356 → 12.184 | 13.190 → 12.935 | 9.020 → 8.945 |
| 2026 (partial) | 12.356 → 12.386 | 12.884 → 12.407 | 9.026 → 8.895 |

The complete-season guard permits at most 0.05 points of MAE regression in any one complete season. The 2023 change is a small regression within that guard; 2024 and the untouched 2025 test improve. The partial 2026 sample is diagnostic only. Expected decimal points are distribution means, not claims about an exact attainable final score.
