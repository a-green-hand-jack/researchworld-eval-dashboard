# SHAP study analysis

**Status:** complete. 27 validated main cells.
Main artifacts: 27/27 valid at source n=120; analyzed n=120, positional slice [0,120) (R=20, P=1,4,16,64). B16: 6/6 valid (first10, seed=11; not additional90).

## Study chronology
Original n30 is exploratory. The uniform additional90 expansion was prespecified AFTER outcome inspection of n30, before expanded outcomes; no cell/model/budget/metric dropped. Combined120 is the main expanded study, not an originally preregistered n120 study. Additional90 are held-out precision validation under the fixed ordering; not a new independently preregistered confirmatory experiment. B16 remains first10 seed11 only.
Analysis stage: **combined120_main**. Original n30 outputs remain unchanged under /work/analysis and archived under /work/analysis30.

## Exact-game macro top-3 match

Equal-weight average over Pima/ACS x LR/RF/MLP; fixed seeds/runs averaged within instance. Intervals are exploratory/descriptive, not certification.

| Method | P | Match | 95% paired cluster CI |
|---|---:|---:|---:|
| antithetic | 1 | 0.765648 | [0.752312, 0.779005] |
| antithetic | 4 | 0.878079 | [0.867453, 0.888172] |
| antithetic | 16 | 0.936574 | [0.928749, 0.944005] |
| antithetic | 64 | 0.965625 | [0.959698, 0.970950] |
| iid_oneway | 1 | 0.574653 | [0.559558, 0.590281] |
| iid_oneway | 4 | 0.756852 | [0.743095, 0.770052] |
| iid_oneway | 16 | 0.864398 | [0.853842, 0.874655] |
| iid_oneway | 64 | 0.929213 | [0.920879, 0.936645] |
| kernel | 1 | 0.445463 | [0.429304, 0.461458] |
| kernel | 4 | 0.710463 | [0.694769, 0.724840] |
| kernel | 16 | 0.841620 | [0.829467, 0.853311] |
| kernel | 64 | 1.000000 | [1.000000, 1.000000] |

## Effect sizes and multiplicity

P64-minus-P1 top-3 match difference: 19.998 percentage points; paired 95% CI [18.863, 21.121]; simultaneous 63-contrast exploratory bootstrap band [14.956, 25.039].
All exact method comparisons and budget-gain contrasts are in paired_comparisons.csv/tex. No uncorrected significance tests or universal reliability declarations are made.

## German: approximate reference diagnostics only

- lr reference_pool_top3_agreement: 0.991667 [0.980556, 1].
- lr pool_difference_l1: 0.00306348 [0.00272288, 0.00341501].
- rf reference_pool_top3_agreement: 0.980556 [0.966667, 0.991736].
- rf pool_difference_l1: 0.002465 [0.00234848, 0.0025906].
- mlp reference_pool_top3_agreement: 0.977778 [0.961111, 0.991667].
- mlp pool_difference_l1: 0.0052044 [0.00493279, 0.00546869].
Pool agreement is convergence evidence, not accuracy against true Shapley values; no formal reference coverage or certification is inferred.

## Background sensitivity (different estimands)

- pima/lr: reference top-3 changes in 5/10 fixed instances; own-target B8 vs B16 top-3 match 0.970 vs 1.000. Full paired intervals and metrics: background_sensitivity.csv/tex.
- pima/rf: reference top-3 changes in 5/10 fixed instances; own-target B8 vs B16 top-3 match 0.935 vs 0.955. Full paired intervals and metrics: background_sensitivity.csv/tex.
- pima/mlp: reference top-3 changes in 4/10 fixed instances; own-target B8 vs B16 top-3 match 1.000 vs 0.985. Full paired intervals and metrics: background_sensitivity.csv/tex.
- acs/lr: reference top-3 changes in 9/10 fixed instances; own-target B8 vs B16 top-3 match 0.935 vs 0.965. Full paired intervals and metrics: background_sensitivity.csv/tex.
- acs/rf: reference top-3 changes in 5/10 fixed instances; own-target B8 vs B16 top-3 match 1.000 vs 0.990. Full paired intervals and metrics: background_sensitivity.csv/tex.
- acs/mlp: reference top-3 changes in 7/10 fixed instances; own-target B8 vs B16 top-3 match 0.930 vs 0.960. Full paired intervals and metrics: background_sensitivity.csv/tex.

## Sample-size illustration, not ACS certification
Bonferroni one-sided Hoeffding over 24 exact antithetic cells: lower=max(0,mean-0.160387). At perfection n=120 reaches at most 0.839613; n>=1235 would be needed for a .95 lower bound at observed perfection under justified sampling assumptions. ACS household PPS-style selection is not justified by the current design.

## Resources

- Main: 27 artifacts; summed CPU 934.138349 s; actual shared cached model rows 502776528; summed cell wall 1615.335063 s (not elapsed parallel makespan).
- B16 sensitivity: 6 artifacts; summed CPU 15.243676 s; actual shared cached model rows 614400; summed cell wall 42.442605 s (not elapsed parallel makespan).
Per-cell held-out AUC, log loss, accuracy, fit warnings and resource counters: resources.csv/tex. Logical per-run uncached row costs: logical_costs.csv/tex. Actual timings/rows include the shared references and all methods, not per-explanation deployment cost.
Measured successful original30+B16+expanded120 campaigns total 1194.679 CPU seconds (0.3319 CPU hours; 1.383% of 24 CPU-hours). Prefix replay is counted as consumed compute; additional90 analysis consumes no new experiment run. Failed runs/overhead are not available.

## Original-prefix/frozen-game audit

Measured prefix status **passed**: 27/27 cells exactly equal across every NPZ array; model parameters, test metrics, manifests and deterministic counters checked. original_prefix_npz_audit.csv and original_prefix_audit.json retain per-array max differences and input hashes. Timings excluded from equality.

## Exploratory first30 / held-out additional90 / combined120

CIs reboot instance clusters at each actual cohort n. Do not pool overlapping cohorts as independent studies.
| Cohort | n | P | Exact macro antithetic match | Descriptive 95% CI |
|---|---:|---:|---:|---:|
| exploratory_first30 | 30 | 1 | 0.751111 | [0.723056, 0.778704] |
| exploratory_first30 | 30 | 4 | 0.869259 | [0.848884, 0.887963] |
| exploratory_first30 | 30 | 16 | 0.929537 | [0.914813, 0.943336] |
| exploratory_first30 | 30 | 64 | 0.962778 | [0.952593, 0.972407] |
| heldout_next90 | 90 | 1 | 0.770494 | [0.753942, 0.786328] |
| heldout_next90 | 90 | 4 | 0.881019 | [0.868817, 0.893274] |
| heldout_next90 | 90 | 16 | 0.938920 | [0.930120, 0.948117] |
| heldout_next90 | 90 | 64 | 0.966574 | [0.959751, 0.973488] |
| combined120_main | 120 | 1 | 0.765648 | [0.752312, 0.779005] |
| combined120_main | 120 | 4 | 0.878079 | [0.867453, 0.888172] |
| combined120_main | 120 | 16 | 0.936574 | [0.928749, 0.944005] |
| combined120_main | 120 | 64 | 0.965625 | [0.959698, 0.970950] |

Compact manuscript tables: paper_antithetic_9cells, paper_exact_macro_controls, paper_german_reference_pools, paper_model_performance, data_splits, paper_gaps_per_budget, paper_sensitivity_first10 (.csv/.tex). Model test metrics are fixed-test observations; prediction-level CIs cannot be recovered from aggregate artifacts.

Resource scope: CPU, total wall and training wall are measured FULL source-run totals, not attributable slice costs. Rows, coalitions and prediction wall are summed over selected instance counters. n90 and n120 resource tables overlap: do not add them. No imputed per-method cost or proportional CPU allocation.

## Metric definitions

- **top3_match:** Unordered set equality of three largest absolute attributions vs target; stable index tie-break; runs then fixed seeds averaged within instance.
- **pairwise_top3_match:** Fraction of the 190 unordered within-game repetition pairs with equal top-3 subsets; average fixed seeds within instance; do not count pairs as samples.
- **reference_top3_overlap:** Mean |estimated top3 intersect reference top3|/3.
- **pairwise_mean_overlap:** Mean pairwise within-game |top3_r intersect top3_s|/3.
- **absolute_l1:** sum_j |estimate_j-reference_j| in probability units; mean over runs.
- **normalized_l1:** Absolute L1 / max(sum_j |reference_j|,0.01), computed per game before averaging.
- **material_sign_agreement:** Fraction of reference features with |phi_j|>=0.01 whose sign is recovered; undefined when none; equal available-seed average within instance and equal valid-instance mean; coverage and valid n reported.
- **nogueira_stability:** 1 - mean_j [R/(R-1)*p_j*(1-p_j)] / [q*(1-q)], R=20, top3 selection frequency p_j and q=3/d. Never clipped; computed per fixed game, then averaged.
- **efficiency_residual:** Mean absolute sum(estimate)-sum(reference); stored max antithetic residual also in resources table.
- **reference_pool_top3_agreement:** German independent 512-cycle pools: top3 equality, not true-reference accuracy.
- **pool_difference_l1:** German sum_j |poolA_j-poolB_j|, probability units.
- **gap_bin:** Reference absolute rank3-minus-rank4 gap: <.002, [.002,.01), >=.01. Per seed-instance game; average selected games using cluster-bootstrap ratios.
- **uncertainty:** 2000 paired instance-cluster bootstrap replicates; same indices within dataset across all methods/models/budgets/fixed seeds. Independent dataset streams. Percentile 2.5/97.5 intervals; undefined bootstrap ratios omitted and counted.
- **exact_macro:** Equal mean over six dataset-model cells (pima/acs x lr/rf/mlp); each seed/run mean within instance; bootstrap instances independently across datasets, shared across models within dataset.
- **multiple_comparisons:** All exact antithetic-minus-controls and P64-minus-P1 contrasts, including macro contrasts, use one 95% max-centered-absolute-deviation paired-bootstrap simultaneous band. Marginal intervals also reported; no unadjusted significance/certification claims.
- **hoeffding:** max(0,mean-sqrt(log(24/.05)/(2*n))), one-sided Bonferroni sample-size illustration over 24 exact antithetic dataset/model/budget cells. ACS sampling assumptions unverified; not an unconditional certificate.
- **costs:** Permutation/iid logical rows per run B*(2+2P*(d-1)); kernel rows capped at B*2**d on full enumeration. Actual cached rows/timings aggregate shared game reference and estimator work. train_seconds/prediction_seconds are wall timings despite names.

## Caveats

- Exploratory/descriptive instance-cluster percentile bootstrap intervals, not finite-sample certificates; 2000 replicates.
- Seeds 11,23,47 are fixed, not sampled model-training replicates; LR seeds are not independent fitted-model evidence.
- Repeated explanations and repetition pairs are not independent instance observations.
- Boundary bootstrap intervals may collapse at 0 or 1; narrow/collapsed intervals do not certify reliability.
- ACS random-person scanning with household deduplication induces unequal household selection; sampling justification is absent. ACS intervals and Hoeffding values are descriptive, not unconditional certificates or survey-weighted population inference.
- German uses an approximate two-pool reference, not ground truth; all German match/error metrics concern reference agreement only, never true accuracy or certification.
- Reference-gap strata are descriptive, oracle-dependent, and conditional on the empirical game; not deployable selectors.
- B16 changes the background and hence the estimand; compare each estimate to its own recomputed target.
- Kernel control is plain constrained least squares without L1 feature selection. At budgets covering the cube it enumerates the full exact game, rather than sampling; cost is capped at 2**d background-averaged rows.
- Cached actual rows and timings include reference construction and all estimators, and cannot be assigned to individual methods or interpreted as deployment timings.
- Cell/seed/gap percentile intervals are marginal descriptive intervals. Effect comparisons additionally receive simultaneous max-deviation bootstrap bands across the reported exact-game contrast family; these bands remain descriptive and may degenerate at boundaries.
- Original n30 is exploratory. The uniform additional90 expansion was prespecified AFTER outcome inspection of n30, before expanded outcomes; no cell/model/budget/metric dropped. Combined120 is the main expanded study, not an originally preregistered n120 study. Additional90 are held-out precision validation under the fixed ordering; not a new independently preregistered confirmatory experiment. B16 remains first10 seed11 only.

## Reproduce / use outputs

```sh
python /work/analyze.py --results /work/results120 --out /work/analysis120 --expected-n 120 --start-instance 0 --stop-instance 120 --sensitivity-results /work/results
python /work/analysis120/plot.py --out /work/analysis120
python /work/analyze.py --self-test
```
- summary.json: numerical results, validation state, definitions, warnings and resource totals.
- cell_summary.csv: full numerical summaries and CIs; cell_summary.tex: compact per-dataset tables. Separate cell_summary_pima/acs/german.tex may be included individually. Booktabs is required.
- exact_macro.csv/tex, per_seed.csv/tex, gap_summary.csv/tex, reference_pool_summary.csv/tex, paired_comparisons.csv/tex, background_sensitivity.csv/tex: corresponding raw numbers and LaTeX. *_raw.tex retains full-column views where compact views are provided.
- budget_accuracy.png, repeatability_accuracy.png, gap_budget.png (+PDF): measured figures. Each matching directory has plot.py, inputs.csv, plot.png/pdf, figure-spec.md and audit.md.
- analysis_inputs.npz: complete source arrays plus every deterministic bootstrap index array. input_metadata.json and validation.json retain metadata and input SHA256 hashes.
- instance_clusters.csv/tex: seed/run-averaged paired cluster observations. contrast_bootstrap.npz: joint contrast replicates in paired_comparisons.csv row order.
- The copied analyze.py can be run with explicit --results and --out paths; original source is /work/analyze.py. --partial exact is opt-in and never labelled a final all-dataset analysis.

## Recommended next experiments (not run here)
1. Prespecify a justified equal-probability household or design-weighted ACS audit before making population-level claims; increase independent instance clusters if certification is the goal.
2. Increase independent German reference-pool budgets and examine remaining top-3 disagreements, retaining all cases and approximate-reference labels.
