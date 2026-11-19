# Evidence for the empirical gain caps (issue #10)

Produced by `python3 code/cap_evidence.py results/cap_evidence` (seed 0, 1000 draws, about 20 s on one CPU). Inputs: `data/processed/ollb6.csv`
(540 fine-tune/base pairs via `mti.data._gains()`, 4,496 unflagged models), `data/processed/helm_mmlu57.csv`. The script asserts that its cap-saturated test
reproduces the feasible counts of the primary closed-form runs (`results/core_ollb.csv`, cap emp99: mean 546, median 451, min 273 of the targets ranked 2 or
lower; `results/core_helm.csv`, caps gain5/10/20).

**Feasibility test.** For rules that are monotone in every score (mean, median, min) a target can become first within the caps iff it is strictly first
(margin eps = 1e-3) at the cap-saturated vector, every task raised to its cap. All counts are over all targets with rank_mean >= 2 on the full board
(OLLB 4,495 targets; HELM 78).

| file | content |
|---|---|
| `pair_bootstrap_draws.csv` | one row per draw: the six emp99 caps and, per rule, n feasible, share, largest feasible mean rank, longest all-feasible prefix |
| `pair_bootstrap_summary.csv` | observed value (all 540 pairs) and 2.5 / 50 / 97.5 percentiles over the draws; the caps' own intervals |
| `loto_allowance.csv` | leave-one-task-allowance-out: that task's gain cap set to 0, the other five at emp99, six-task rule unchanged; observed and bootstrap percentiles (same draws) beside the primary values |
| `joint_gains.csv` | descriptive, in-sample joint structure of the 540 gain vectors (a description of what fine-tunes did, not a model of attainable gains) |
| `helm_transfer_sensitivity.csv` | uniform allowance h on all 57 HELM subjects: the six OLLB emp99 gains and gain5/10/20; target-bootstrap intervals on the share |

**Pair bootstrap.** The 540 pairs are resampled jointly across tasks (each draw keeps a pair's six gains together); per-task emp99 caps are recomputed on
each draw and every target is retested. This propagates the uncertainty of the cap estimate; it does not model uncertainty of the *population* of fine-tunes
beyond these 540 pairs, nor the choice of the 99th percentile (see `results/summary` for the emp95 and ceiling alternatives).

**Leave-one-task-allowance-out.** Zeroing a task's allowance removes that task's allowance only; the other five tasks keep their emp99 allowances. The caps remain observed percentiles,
so this is a sensitivity to which task carries the allowance, not an estimate of a different population.

**Joint gains.** `joint_gains.csv` counts pairs with a gain above half of the task's emp99 cap on at least k tasks, whether a whole vector approaches all
marginal caps, negative gains, and the correlation of task gains. The saturated cap vector requires every task at its 99th-percentile gain at once; no
observed pair has all six gains at or above their caps (row `n_pairs_all_six_gains_ge_cap`), and the largest fraction of its cap that the weakest task of
any pair reaches is in `max_over_pairs_of_min_task_cap_fraction`. Descriptive; it cannot show that the saturated vector is unattainable.

**HELM transfer.** The OLLB gains are measured on six different benchmarks and applied uniformly to 57 MMLU subjects; they are arbitrary transferred
allowances, not estimates for HELM. The row `ollb_emp99_MMLU-PRO` (7.06) is the primary HELM cap (emp99T), the IFEval row (63.0) makes every target feasible by construction of a
very large allowance.

## Results (OLLB, 4,495 targets ranked 2 or lower; observed with all 540 pairs, then the 2.5-97.5 percentile range over 1000 pair-bootstrap draws)
| rule | feasible targets | feasible share | largest feasible mean rank | longest all-feasible prefix |
|---|---|---|---|---|
| mean | 546 (503-747) | 12.1% (11.2-16.6%) | 901 (824-1201) | 394 (346-590) |
| median | 451 (368-550) | 10.0% (8.2-12.2%) | 1207 (1207-1634) | 90 (70-216) |
| min | 273 (224-293) | 6.1% (5.0-6.5%) | 2225 (1464-2225) | 5 (4-6) |

The bootstrap range is asymmetric because the 99th percentile of 540 gains rests on its 5-6 largest values (BBH cap 12.1, range 9.4-20.4; MMLU-PRO 7.1, range 5.5-11.0;
IFEval 63.0, range 60.9-64.1; MATH 25.7; GPQA 6.4; MuSR 12.1). Leaving one task's allowance out (`loto_allowance.csv`, observed feasible targets with the primary value in brackets): without
IFEval the mean rule has 150 (546), the median 337 (451), the min 242 (273); without MATH 256 (546), 37 (451), 259 (273); without BBH 462, 114, 273; without GPQA 499, 451, 11 (min: GPQA is
the binding task for the min rule); without MUSR 465, 451, 54; without MMLU-PRO 495, 193, 273. The IFEval and MATH allowances carry most of the mean-rule feasibility.
Joint gains (`joint_gains.csv`): 99 of the 540 pairs gain more than half of the task's emp99 cap on at least 2 tasks (35 when IFEval is left out), 18 on at least 3, 7 on at least 4, 4 on at least 5, none on all 6;
7 pairs exceed 0.9 of the cap on at least 2 tasks, none on 5 or more; no pair reaches every marginal cap, and the pair whose weakest task is furthest along reaches 24.5% of its cap there.
521 of the 540 pairs lose points on at least one task (negative gains on IFEval 140, BBH 280, MATH 229, GPQA 277, MuSR 358, MMLU-PRO 401 pairs). The largest total gain of any pair is 103.8 points
(sum of the six caps 126.3; median pair 7.3). The cap-saturated vector (all six tasks at their 99th-percentile gain at once) is therefore well beyond what any single observed pair did;
feasibility by the saturated vector is a statement about a deliberately generous allowance set, as the report says.
HELM (78 targets; `helm_transfer_sensitivity.csv`; share feasible for mean / median / min): allowance 6.4 (GPQA gain) 18% / 28% / 12%; 7.1 (the primary emp99T) 19% / 33% / 12%; 12.1 (BBH, MuSR) 46% / 58% / 23%;
25.7 (MATH) 87% / 88% / 64%; 63.0 (IFEval) 100% / 100% / 100%; comparators gain5 14% / 21% / 9%, gain10 37% / 51% / 18%, gain20 72% / 85% / 44%. These are arbitrary transferred allowances.
