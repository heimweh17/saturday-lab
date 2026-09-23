# Model 5 review results

Four-stage retrospective research; no school-specific adjustment or FPI target fitting. All inspected years and revised-source limitations remain explicit.

## Decision

Publish one scalar-strength model, with recruiting confined to a preseason scoring prior. The current selected probability inputs are opponent-adjusted scoring, prior observed-passer efficiency, venue and rest. This fixes opponent-dependent talent decay and makes neutral rankings coherent. Selection within each specified search uses earlier-year log loss, not desired school ranks. Structural clarity and current performance support this version, but retrospective evidence does not establish overall predictive superiority.

## Same-game outcomes

| Season | Model | Games | Accuracy | Brier | Log loss |
|---|---|---:|---:|---:|---:|
| 2023 | Saturday model | 792 | 72.8535% | 0.178075 | 0.528411 |
| 2023 | Previous v4 | 792 | 73.4848% | 0.180382 | 0.536088 |
| 2023 | Previous v3 | 792 | 72.9798% | 0.182239 | 0.541344 |
| 2023 | Original scoring benchmark | 792 | 72.8535% | 0.180746 | 0.537716 |
| 2024 | Saturday model | 798 | 69.1729% | 0.190021 | 0.554071 |
| 2024 | Previous v4 | 798 | 68.5464% | 0.187761 | 0.549656 |
| 2024 | Previous v3 | 798 | 68.1704% | 0.191290 | 0.559040 |
| 2024 | Original scoring benchmark | 798 | 68.6717% | 0.192332 | 0.561882 |
| 2025 | Saturday model | 808 | 72.4010% | 0.179756 | 0.532035 |
| 2025 | Previous v4 | 808 | 73.0198% | 0.180808 | 0.535112 |
| 2025 | Previous v3 | 808 | 72.5248% | 0.181424 | 0.537666 |
| 2025 | Original scoring benchmark | 808 | 72.1535% | 0.179198 | 0.531382 |
| 2026 | Saturday model | 157 | 82.1656% | 0.134937 | 0.428455 |
| 2026 | Previous v4 | 157 | 81.5287% | 0.135320 | 0.433280 |
| 2026 | Previous v3 | 157 | 80.2548% | 0.149441 | 0.469123 |
| 2026 | Original scoring benchmark | 157 | 82.1656% | 0.144765 | 0.460080 |

2024–25 v5 and v4 both correctly predict 1,137/1,606 games; original 1,131. V5 pooled log loss .542984 is slightly worse than v4 .542339 and better than original .546537. No uniform improvement claim.

## Recruiting hypothesis

These are each mode’s best earlier-year validation results for the 2026 selection, before passer-context extensions. Reoptimization means these are alternatives, not causal effects of redshirting.

| Recruiting mode | Best validation log loss | Candidates |
|---|---:|---:|
| none | 0.5417353 | 96 |
| published | 0.5362668 | 192 |
| equal | 0.5368170 | 192 |
| developmental | 0.5370056 | 192 |
| no_freshmen | 0.5371767 | 192 |
| lagged_four | 0.5371843 | 192 |

No evidence here warrants automatically excluding all freshmen. Class-age proxies cannot identify actual redshirts or current rosters. Game-roster participation flags were not usable; published passing-box validation counts remain in model.json.

## Descriptive uncertainty

- [2024, 2025], new minus v4 log loss: 0.000646, week-bootstrap 95% interval [-0.007873, 0.008652], 34 weeks. Three current-season weeks cannot establish long-run superiority.
- [2024, 2025], new minus original log loss: -0.003552, week-bootstrap 95% interval [-0.013479, 0.005349], 34 weeks. Three current-season weeks cannot establish long-run superiority.
- [2026], new minus v4 log loss: -0.004825, week-bootstrap 95% interval [-0.006822, -0.000866], 3 weeks. Three current-season weeks cannot establish long-run superiority.
- [2026], new minus original log loss: -0.031625, week-bootstrap 95% interval [-0.051408, -0.021559], 3 weeks. Three current-season weeks cannot establish long-run superiority.

## Diagnostic rankings

Florida moves 18 preseason → 16 → 13 → 13. Beating Auburn improves its own scalar strength; the rank stays 13. Houston finishes this snapshot 42 versus v4 51 and dated FPI 31; JMU 44 versus v4 36 and FPI 59. These are observed consequences, not targets.

FPI mean absolute rank gap: 8.6812 → 7.5942; Spearman .9543 → .9674. Model results through September 20, 2026; FPI September 22. Agreement is not evidence of superior forecasting.

All candidates, source hashes, cutoffs and predictions are in public/data/model.json and research-stage1/2/3.json. Protocols and blueprint documents are in analytics/.
