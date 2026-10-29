# Analysis: validity audit of the experimental log

Source: `experimental_log.md` as embedded in `/initial-state/inputs/0/INSTRUCTIONS.md` (the only data; no new
experiments are run, because the task requires every reported number to match the log).
All numbers below are % points. Scripts are deterministic: `python3 -I build_results.py`,
`python3 -I digitize_figure1.py /initial-state/inputs/2/figure_1.png`.

Files: `results_tables.csv` (verbatim transcription of all log tables), `gap_audit.csv` (every logged
"Performance Gap" row recomputed), `figure1_readout.csv` / `figure1_gaps.csv` (approximate bar read-out of `figures/figure_1.png`).

## A. Verified facts
1. All 9 CIFAR-10 gap rows (forget size, perturbations, lambda) equal |Unlearned(-) - Retrained| exactly.
2. **The 3 CIFAR-100 mixed-linear gap rows do NOT compare with Retrained.** They equal |Unlearned(-) - Unlearned(+)|
   (all 12 entries reproduce exactly). Against Retrained the gaps are:

   | forget | test | remaining | forget acc | MIA |
   |---|---|---|---|---|
   | 20% | 2.2 | 4.3 | 0.6 | 0.8 |
   | 15% | 1.7 | 1.2 | 1.1 | 1.5 |
   | 10% | 0.9 | 1.9 | 2.7 | 2.3 |

   So "gap 0.1-0.5 on test accuracy" (log, qualitative obs. on neural networks) is the gap to Unlearned(+), i.e. it says the
   estimated Hessian is as good as the exact one; it is **not** a gap to retraining. Paper must label the column "gap to Unlearned(+)"
   or report the Retrained gaps above. Do not write that the mixed-network gap to Retrained is 0.1-0.5.
3. In the mixed-linear table Unlearned(-) remaining accuracy (70.0, 70.1, 70.1 at 20/15/10%) is above Retrained at 20% and 15%
   (65.7, 68.9) and above Unlearned(+) there by 6.6 and 2.2 points, but below both at 10% (72 / 72.5). Remaining accuracy is
   the weakest-matching metric and its error is not sign-consistent, so do not write that every metric is approximated well.
4. Row `10% forget / 500 perturbations / lambda=0` is the same configuration and the same numbers (70/71/68/51.4) in three
   tables: it is the default setting (forget 10%, 500 perturbations, lambda=0), so the three ablations share one point.
   Retrained rows differ slightly between tables (e.g. 5%: 73/74/73/49.4; 15%: 73/75/73/50), as expected because the retained set changes.

## B. What the log supports, and how strongly
| Claim in log | Verdict from the numbers |
|---|---|
| Unlearned(-) ~ Retrained "consistently" | **Partly.** True at CIFAR-10 5% (gap 0), 10% (2/3/4/1.4), 1000 perturbations (0/0/1/1), lambda 0.001 (0/1/0/0.9). False at 15% forget (14/15/14/5.8) and 250 perturbations (15/16/15/6.2). Mixed-linear: 0.9-2.2 test gap to Retrained. Say "comparable in the default regime", not "consistently". |
| Gap widens with forget size | Supported on one axis, 3 points, 1 run: test gap 0 -> 2 -> 14 for 5/10/15%. The 10->15% jump (12 pts) is far larger than 5->10 (2 pts), so a threshold/breakdown is a better description than a smooth trend. The "aligns with the theoretical bound" statement cannot be checked: no bound is given in the materials; phrase it as qualitative consistency, state no constant or rate. |
| More perturbations help | Supported, monotone on all four metrics: test gap 15 -> 2 -> 0 for 250/500/1000. 3 points. Note at 250 the Unlearned(-) model is far *worse* than at 500 (57% vs 70% test), i.e. the estimator has a sharp sample-size requirement. |
| Larger lambda reduces the gap | Supported for test/remaining/forget (2->1->0, 3->2->1, 4->1->0), **not monotone for MIA** (1.4, 0.2, 0.9). Only 3 lambda values (0, 0.0005, 0.001), all tiny; "inversely proportional to lambda^2" is a theory statement not testable from 3 points: do not claim it was "confirmed", say "consistent with". |
| Beats NegGrad/RandomLabels/JiT/Adversarial | Supported on utility: test 70 vs 51.5-52.1 (RandomLabels 20.6); Remaining 71 vs 52.7-53.2; Forget 68 vs 51.0-51.2. MIA: all methods are within 3 pts of 50 (47-51.4), so MIA does **not** discriminate (RandomLabels, at 20.6% accuracy, has MIA 47). Support the claim on accuracy-to-Retrained, not on MIA. Distance to Retrained forget acc (72): ours 4, others ~21 (RandomLabels 50.6). |
| Unlearned(-) ~ Unlearned(+) on four datasets (Fig. 1) | Supported by the figure; read-out below (approx. +-1). Largest gap(-)vs(+): 3.6 (Caltech256 forget), 3.3 (Dogs remaining); 2.2 (CIFAR-10 forget) etc. |
| Unlearned(-)/(+) ~ Retrained on four datasets (Fig. 1) | **Weaker than the caption says.** From the read-out (`figure1_gaps.csv`): Unl(-) vs Retrained test acc gap is 2.2 (CIFAR-10), 4.4 (CIFAR-100), 4.4 (Dogs), 5.1 (Caltech256); forget acc gap 4.0, 7.2, 6.2, 6.6. Unl(+) is just as far (up to 10.2 on Caltech256 forget). The Newton step itself (exact Hessian) leaves a 2-7 point residual vs retraining: this is not caused by Hessian estimation. MIA is within ~1.8 of retrained everywhere. Honest statement: MIA indistinguishable (<=~2 pts); accuracy 2-7 pts below retraining, same for the exact-Hessian variant. |

Also: Unlearned(-) forget accuracy is below Retrained forget accuracy everywhere (CIFAR-10 68 vs 72, etc.): the forget-set accuracy of
the retrained model is *not* zero (forget data are i.i.d. with test data), so "forget accuracy" is correctly compared to the retrained model, not to chance. Say this explicitly.

## C. Limits that must be disclosed
- Single run per cell, no seeds, no confidence intervals. Entries are integers for CIFAR-10 (1-pt resolution), so gaps <=1 pt are not
  interpretable. For scale only: a binomial s.e. for a 10,000-image test set at p=0.72 is ~0.45 pt (dataset split size assumed, not in log).
- The numerical gaps are measured between models, not between estimated and true Hessian: the log has **no direct Hessian error**
  measurement; the claim "validating a more accurate Hessian approximation" is an inference from downstream accuracy (perturbations ablation).
- Figure 1 has no numbers in the log except CIFAR-10 (matches the CIFAR-10 table within 0.9 pt; e.g. Retrained MIA reads 49.1 vs 50). Other
  panel values are visual read-outs (+-1 pt; CIFAR-100 Remaining bars sit on a gridline, 59-60). The CIFAR-100 panel (Retrained test ~55) is a
  different model from the mixed-linear table (Retrained test 63.7 at 10%): the figure appears to be the plain linear classifier; the log does not say
  so. Do not cite numbers read from the figure in the text as measured values, and don't say the figure is the mixed network.
- Unlearned(+) has no CIFAR-10 row in any table; it appears only in Fig. 1 (read-out ~70.2/72.4/70.2/49.5) and the mixed-network table.
- Stanford Dogs / CalTech-256 appear only in Fig. 1. MIA definition (attack model, features) and the baselines' hyper-parameters are not in the log.
  Linear-classifier accuracy (~72% on CIFAR-10) reflects frozen ImageNet ResNet-18 features; absolute accuracies are not state of the art and need not be.
- Forget sets: the claim is instance-level (random samples), supported only by random subsets of 5-20%; no class-level or tiny (<5%) forget sets
  were run, so no statement about single-sample or small-batch deletion.
- The log gives Unlearned(+) / Unlearned(-) no timing, so no efficiency claim can be made.
