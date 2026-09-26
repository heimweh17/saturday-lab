# Home-field audit results

**Decision: `retain-v6`.** The predeclared gate did not pass, so production v6 is unchanged.

## Free coefficient by target season

| Target | Coefficient | Equal-team home win probability |
|---:|---:|---:|
| 2023 | 0.3224 | 58.0% |
| 2024 | 0.3199 | 57.9% |
| 2025 | 0.3204 | 57.9% |
| 2026 | 0.3270 | 58.1% |

## Fixed-coefficient selection (2023-2024)

| Variant | Log loss | Brier | Accuracy |
|---|---:|---:|---:|
| free | 0.536353 | 0.181794 | 72.3% |
| fixed_0.15 | 0.538645 | 0.182478 | 71.7% |
| fixed_0.20 | 0.537472 | 0.182063 | 71.8% |
| fixed_0.25 | 0.536716 | 0.181827 | 71.9% |
| fixed_0.30 | 0.536373 | 0.181767 | 72.1% |

## Pooled completed seasons (2023-2025)

| Model | Log loss | Brier | Accuracy | Near-even predicted | Near-even actual |
|---|---:|---:|---:|---:|---:|
| Free v6 | 0.534297 | 0.180826 | 72.5% | 57.9% | 57.6% |
| fixed_0.30 | 0.534372 | 0.180816 | 72.4% | 57.4% | 57.6% |

The near-even sample's 95% Wilson interval for the actual home win rate is 53.5%–61.6%.

## Promotion gate

- Selected fixed candidate: `fixed_0.30`.
- Pooled log-loss improvement: -0.000075.
- Pooled Brier improvement: +0.000010.
- Worst single-season log-loss regression: +0.000184.
- Week-block bootstrap probability of lower log loss: 17.9%.
- Near-even absolute calibration improvement: +0.001843.
- 2025 confirmation log-loss improvement: -0.000184.
- 2025 confirmation accuracy change: -0.1%.

## Feature-set diagnostic

| Target | Score only | Baseline + passer | Stable pair | Broad v6 |
|---:|---:|---:|---:|---:|
| 2023 | 0.3069 | 0.3079 | 0.3173 | 0.3224 |
| 2024 | 0.3031 | 0.3041 | 0.3125 | 0.3199 |
| 2025 | 0.3035 | 0.3044 | 0.3129 | 0.3204 |
| 2026 | 0.3118 | 0.3127 | 0.3206 | 0.3270 |

The feature-set table is a double-counting diagnostic: a sharp collapse or jump after adding efficiency inputs would indicate that those inputs are absorbing venue in an unstable way. It is evidence, not a causal proof.

Integrity check: maximum difference between the reconstructed 2026 coefficient vector and the published vector was 0.

This is a retrospective audit of seasons already inspected during model development. The 2026 sample is incomplete and is not used for promotion.
