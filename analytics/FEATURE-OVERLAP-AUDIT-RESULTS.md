# Feature overlap, confidence and rest audit results

**Decision: `retain-v6`.** The frozen gate failed, so production v6 is unchanged.

## Earlier-season selection (2023-2024)

| Variant | Log loss | Brier | Accuracy |
|---|---:|---:|---:|
| broad_ridge_1 | 0.536353 | 0.181794 | 72.3% |
| broad_ridge_10 | 0.536526 | 0.181811 | 72.4% |
| broad_nonlinear_rest | 0.536956 | 0.182057 | 72.1% |
| temperature_0.95 | 0.537052 | 0.181891 | 72.3% |
| temperature_0.90 | 0.538255 | 0.182143 | 72.3% |
| broad_ridge_50 | 0.538389 | 0.182337 | 72.1% |
| compact_ridge_1 | 0.538610 | 0.182807 | 72.2% |
| stable_pair_ridge_1 | 0.538610 | 0.182807 | 72.2% |
| compact_ridge_10 | 0.538992 | 0.182903 | 72.1% |
| stable_pair_ridge_10 | 0.538992 | 0.182903 | 72.1% |
| compact_nonlinear_rest | 0.539200 | 0.183068 | 72.0% |
| temperature_0.85 | 0.539995 | 0.182573 | 72.3% |

## Completed-season comparison (2023-2025)

| Model | Log loss | Brier | Accuracy |
|---|---:|---:|---:|
| broad_ridge_1 | 0.534297 | 0.180826 | 72.5% |
| broad_ridge_10 | 0.534658 | 0.180931 | 72.6% |

## Favorite calibration

### broad_ridge_1

| Favorite band | Games | Mean prediction | Actual wins | Upsets |
|---|---:|---:|---:|---:|
| 50-60% | 584 | 55.0% | 56.5% | 43.5% |
| 60-70% | 582 | 65.0% | 65.5% | 34.5% |
| 70-80% | 521 | 74.9% | 73.9% | 26.1% |
| 80-85% | 218 | 82.6% | 84.4% | 15.6% |
| 85-90% | 198 | 87.5% | 87.9% | 12.1% |
| 90-95% | 179 | 92.5% | 95.0% | 5.0% |
| 95-100% | 116 | 96.9% | 99.1% | 0.9% |

### broad_ridge_10

| Favorite band | Games | Mean prediction | Actual wins | Upsets |
|---|---:|---:|---:|---:|
| 50-60% | 592 | 55.0% | 57.3% | 42.7% |
| 60-70% | 583 | 64.9% | 65.7% | 34.3% |
| 70-80% | 524 | 74.8% | 73.1% | 26.9% |
| 80-85% | 214 | 82.5% | 86.0% | 14.0% |
| 85-90% | 202 | 87.5% | 88.1% | 11.9% |
| 90-95% | 176 | 92.5% | 94.9% | 5.1% |
| 95-100% | 107 | 96.9% | 99.1% | 0.9% |

## Promotion gate

- Selected candidate: `broad_ridge_10`.
- Pooled log-loss improvement: -0.000361.
- Pooled Brier improvement: -0.000104.
- 2025 log-loss improvement: -0.000733.
- 2025 accuracy change: -0.1%.
- Worst completed-season log-loss regression: +0.000733.
- Bootstrap probability of lower log loss: 31.3%.
- Baseline/candidate extreme-band calibration error: 0.0240 / 0.0229.

The coefficient reconstruction matched the released production vector exactly. This is retrospective evidence, and partial 2026 results did not participate in promotion.
