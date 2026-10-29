# Admissible facts and checks (draft; see wiki Brief for the quoted requirements)
Source of every number: experimental_log.md embedded in /initial-state/inputs/0/INSTRUCTIONS.md (lines 338-417) and figures/figure_1.png.
Format per row: Test / Remaining / Forget accuracy (%) / MIA (%).

## Recomputed gaps (|Retrained - Unlearned(-)|) — verified against the log
- Forget size, CIFAR-10: 15%: R 73/75/73/50 vs U- 59/60/59/55.8 -> 14/15/14/5.8 (log ok); 10%: R 72/74/72/50 vs 70/71/68/51.4 -> 2/3/4/1.4 (ok); 5%: R 73/74/73/49.4 vs 73/74/73/49.4 -> 0/0/0/0 (ok).
- Perturbations (R 72/74/72/50): 250: 57/58/57/56.2 -> 15/16/15/6.2 (ok); 500: 70/71/68/51.4 -> 2/3/4/1.4 (ok); 1000: 72/74/71/49 -> 0/0/1/1 (ok).
- Lambda (R 72/74/72/50): 0: 70/71/68/51.4 (2/3/4/1.4); 0.0005: 71/72/71/49.8 -> 1/2/1/0.2; 0.001: 72/73/72/50.9 -> 0/1/0/0.9 (all ok).
- Default configuration = the 10% / 500 perturbations / lambda=0 row (same numbers in three tables) — inferred.

## Mixed linear networks (CIFAR-100): "Performance Gap" in the log is vs Unlearned(+), NOT vs Retrained
| forget | Retrained | Unl(+) | Unl(-) | log gap | gap vs Unl(+) | gap vs Retrained |
| 20% | 62.2/65.7/62.6/50 | 60.1/63.4/59.3/50.4 | 60/70/63.2/50.8 | 0.1/6.6/3.9/0.4 | 0.1/6.6/3.9/0.4 | 2.2/4.3/0.6/0.8 |
| 15% | 63.1/68.9/63.3/50.2 | 61.9/67.9/62.2/50.7 | 61.4/70.1/62.2/51.7 | 0.5/2.2/0.0/1.0 | 0.5/2.2/0.0/1.0 | 1.7/1.2/1.1/1.5 |
| 10% | 63.7/72/63.9/50 | 63.3/72.5/64.9/51 | 62.8/70.1/61.2/52.3 | 0.5/2.4/3.7/1.3 | 0.5/2.4/3.7/1.3 | 0.9/1.9/2.7/2.3 |

## Source-free baselines (CIFAR-10, linear, 10%): see Brief s.3; Unlearned(-) 70/71/68/51.4 vs NegGrad 51.9/53.2/51.2/48, Random Labels 20.6/21.6/21.4/47, JiT 52.1/53.1/51.1/49.1, Adversarial 51.5/52.7/51.0/50.0, Retrained 72/74/72/50.
(Remark: the baseline row for Unlearned(-) reuses the default run. MIA of Random Labels/NegGrad 47-48 is *below* 50.)

## Figure 1: approximate bar heights (read by eye; not log values) — usable only qualitatively.
