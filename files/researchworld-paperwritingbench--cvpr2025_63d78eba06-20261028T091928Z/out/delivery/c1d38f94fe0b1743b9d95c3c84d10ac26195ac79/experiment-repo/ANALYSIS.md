# Analysis of the experimental log (audit of what the claims may rest on)

No new experiments exist or are allowed: the paper may report only the logged numbers. Analysis here =
(1) transcription of all logged tables, (2) recomputation of every logged "Performance Gap", (3) digitization of
`figures/figure_1.png` (bars read from pixels; calibration check against the logged CIFAR-10 10% row: error <= ~0.8 pt),
(4) claim-by-claim check of the log's "qualitative observations".

Files: `results/log_tables.csv` (logged values, verbatim), `results/gap_audit.csv` (gap recomputation),
`results/figure1_digitized.csv` (approximate, **estimates**, +-1 pt), scripts `analysis/audit_logs.py`, `analysis/digitize_fig1.py`.

## A. Definition of "Performance Gap" is not uniform (must be stated in the paper)
* CIFAR-10 ablations (forget size, perturbations, lambda): gap = |Unlearned(-) - Retrained| exactly, every cell.
* Mixed-linear CIFAR-100 table: gap = |Unlearned(-) - **Unlearned(+)**| in every cell, *not* vs Retrained.
  Gap vs Retrained (recomputed, pts), test/remaining/forget/MIA: 20%: 2.2/4.3/0.6/0.8; 15%: 1.7/1.2/1.1/1.5; 10%: 0.9/1.9/2.7/2.3.
  The log's "0.1-0.5% test gap" is therefore a gap to Unlearned(+); vs Retrained it is 0.9-2.2 pts. Report both, label the reference.

## B. Claim check (log observation -> what the numbers support)
| Log claim | Verdict |
|---|---|
| U(-) comparable to Retrained, all 4 datasets, 10% forget | Holds for CIFAR-10 (test 70 vs 72). **Not for the other three** in Fig. 1 (digitized, linear head): test Retrained vs U(-) = CIFAR-100 ~55.5 vs ~51, StanfordDogs ~58.6 vs ~54.4, Caltech256 ~53.7 vs ~48.7 (gap ~4-5 pts); forget acc ~7 pts (CIFAR-100), ~6 (Dogs), ~6 (Caltech) below Retrained. Say "within ~5 pts", not "closely matches". MIA within ~1.5 pts everywhere. |
| U(-) matches U(+) | Supported: test-acc differences <= ~1.8 pts, forget <= ~3.5 pts (Caltech); U(-) is sometimes *above* U(+) (CIFAR-100 test, Dogs remaining). Fig. 1 itself has no CIFAR-100 "mixed" numbers; its CIFAR-100 Retrained (~55.5) differs from the mixed-linear table (62-64), so Fig. 1 is a different (linear-head) model - say so. |
| Gap widens with forget size (5->15%) "as theory predicts" | Direction supported (test gap 0 -> 2 -> 14). The shape is a cliff between 10% and 15%, from 3 points, one run: do not claim a fitted/quantitative agreement with the bound. At 15%, U(-) test/remaining/forget = 59/60/59 (uniform ~14-pt drop, MIA 55.8): unlearning has *failed* there, report as a limitation. |
| More perturbations help (250/500/1000) | Supported in direction (test gap 15 -> 2 -> 0; MIA gap 6.2 -> 1.4 -> 1.0). 3 points, single run. The perturbations study uses only the 10% forget set; no run varies perturbations at other forget sizes, so a perturbations-to-forget-size interaction was not tested and must not be claimed. Both failures (250 perturbations; 15% forget) show a similar uniform ~14-15 pt drop. |
| Larger lambda shrinks gap; "confirms bound ~ 1/lambda^2" | Accuracy gaps are monotone (test 2/1/0, remaining 3/2/1, forget 4/1/0) but MIA gap is not (1.4/0.2/0.9). 3 lambda values, 1-pt resolution: supports "larger lambda helped here"; **cannot** confirm a 1/lambda^2 rate. |
| Outperforms source-free baselines | Utility: clearly (test 70 vs 51.5-52.1 for NegGrad/JiT/Adversarial, 20.6 Random Labels). MIA gap to 50: Adversarial 0.0, JiT 0.9, U(-) 1.4, NegGrad 2.0, RandomLabels 3.0 -> U(-) is **not best on MIA**; wording "MIA close to 50%" holds, "best MIA" does not. Baseline hyper-parameters/tuning are not logged (comparison is one setting: linear classifier, CIFAR-10, 10%). |

## C. Other points the paper must respect
* Single run per cell, no seeds/CIs/variances anywhere; values are integers for CIFAR-10 (1-pt resolution). No significance claims. Planning estimate only (not logged): binomial SE of an accuracy near 70% on a 10k-image set is ~0.5 pt, on a 2.5k-image forget set ~0.9 pt - differences of 1-2 pts are within noise-like scale.
* The 10%/500 perturbations/lambda=0 rows are the same configuration (identical numbers in three tables); treat as the default setting, not independent evidence.
* Retrained rows differ between tables (72/74/72/50, 73/75/73/50, 73/74/73/49.4): retrained model per forget set.
* Stanford Dogs and CalTech-256 appear only in Fig. 1; no table numbers are logged for them. Quote them only as figure-read approximations ("~") or not at all.
* Not logged, so not to be stated: Hessian dimension, SDP solver/runtime, number of seeds, test-set sizes, the theoretical bounds' form (idea.md promises bounds but gives none), "statistically indistinguishable" guarantees. The Hessian estimation uses the forget set + Gaussian perturbations (idea.md); no result tests the "locally smooth" assumption.
* CIFAR-100 mixed-linear: U(-) remaining accuracy (70.0/70.1/70.1) is above Retrained at 20% and 15% (65.7, 68.9) and above U(+) by 6.6 pts at 20%, while forget accuracy (63.2) is 7 pts below remaining; Retrained's remaining-forget spread is 3 pts. Report as-is; do not present as an improvement over retraining.

## D. Figure 1 values and gap statistics (answers `paper-repo`#3, `figtab-repo`#2, `story-repo`#4)
* `results/figure1_digitized.csv` / `results/figure1_gaps.csv` (script `analysis/fig1_gaps.py`): bar heights read from pixels. Read-off check on CIFAR-10 against the logged Retrained and Unlearned(-) values: error -0.2 to -0.6 pt (slight systematic under-read); quote as "~" to the nearest point, uncertainty +-1 pt. Unlearned(+) CIFAR-10 and all CIFAR-100 (linear head)/Dogs/Caltech values exist only as bars: no log source; figure-read estimates only.
* Mean over the 4 datasets of |Unlearned(-) - Retrained| (pts, estimates): test 3.9, remaining 2.2, forget 5.8, MIA 1.2. For the exact-Hessian Unlearned(+): test 4.8, remaining 2.6, forget 6.5, MIA 1.0. Mean |U(-) - U(+)|: 1.0, 1.4, 1.8, 0.9. So the source-free estimate tracks the exact-Hessian update closely, and **both** sit ~4-6 pts below Retrained on test/forget accuracy (the largest part of the shortfall is not due to the Hessian estimate). MIA is ~50% (within ~1.8 pt) for all three.
* Definitions (from the log only): accuracies in %; MIA is a score in % where ~50% = indistinguishable (the attack type/features are not logged). Remaining = accuracy on the retained training data; Forget = on the forgotten samples; Test = held-out test. The forget accuracy of Retrained ~ its test accuracy, as expected for a model that never saw the forget set.
* Cannot be said: any variance/seed statement, significance, test-set sizes, baselines on Dogs/Caltech/CIFAR-100, whether Fig. 1's CIFAR-100 is the mixed-linear model (its Retrained ~55 differs from 62-64 in the mixed table: it is not).
* Answers to `figtab-repo`#2: all three points confirmed; I hold no extra runs or seeds. Answers to `story-repo`#4: (1) section A and `results/gap_audit.csv`; (2) duplicated config in "C"; (3) section B.
