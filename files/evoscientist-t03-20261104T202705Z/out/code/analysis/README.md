# SHAP study analysis

**Status:** complete. 27 validated main cells.
Main artifacts: 27/27 valid (n=30, R=20, P=1,4,16,64). B16: 6/6 valid (n=10, seed=11).

## Exact-game macro top-3 match

Equal-weight average over Pima/ACS x LR/RF/MLP; fixed seeds/runs averaged within instance. Intervals are exploratory/descriptive, not certification.

| Method | P | Match | 95% paired cluster CI |
|---|---:|---:|---:|
| antithetic | 1 | 0.751111 | [0.723056, 0.778704] |
| antithetic | 4 | 0.869259 | [0.848884, 0.887963] |
| antithetic | 16 | 0.929537 | [0.914813, 0.943336] |
| antithetic | 64 | 0.962778 | [0.952593, 0.972407] |
| iid_oneway | 1 | 0.559259 | [0.526940, 0.592593] |
| iid_oneway | 4 | 0.752407 | [0.725185, 0.780373] |
| iid_oneway | 16 | 0.855278 | [0.834532, 0.875282] |
| iid_oneway | 64 | 0.922037 | [0.907308, 0.936113] |
| kernel | 1 | 0.441667 | [0.408611, 0.475377] |
| kernel | 4 | 0.705185 | [0.672868, 0.739630] |
| kernel | 16 | 0.833981 | [0.810646, 0.857410] |
| kernel | 64 | 1.000000 | [1.000000, 1.000000] |

## Effect sizes and multiplicity

P64-minus-P1 top-3 match difference: 21.167 percentage points; paired 95% CI [18.805, 23.454]; simultaneous 63-contrast exploratory bootstrap band [11.275, 31.058].
All exact method comparisons and budget-gain contrasts are in paired_comparisons.csv/tex. No uncorrected significance tests or universal reliability declarations are made.

## German: approximate reference diagnostics only

- lr reference_pool_top3_agreement: 1 [1, 1].
- lr pool_difference_l1: 0.00282642 [0.00239245, 0.00338855].
- rf reference_pool_top3_agreement: 0.988889 [0.966667, 1].
- rf pool_difference_l1: 0.0023411 [0.00213667, 0.00256365].
- mlp reference_pool_top3_agreement: 0.977778 [0.944444, 1].
- mlp pool_difference_l1: 0.004961 [0.00447401, 0.00551872].
Pool agreement is convergence evidence, not accuracy against true Shapley values; no formal reference coverage or certification is inferred.

## Background sensitivity (different estimands)

- pima/lr: reference top-3 changes in 5/10 fixed instances; own-target B8 vs B16 top-3 match 0.970 vs 1.000. Full paired intervals and metrics: background_sensitivity.csv/tex.
- pima/rf: reference top-3 changes in 5/10 fixed instances; own-target B8 vs B16 top-3 match 0.935 vs 0.955. Full paired intervals and metrics: background_sensitivity.csv/tex.
- pima/mlp: reference top-3 changes in 4/10 fixed instances; own-target B8 vs B16 top-3 match 1.000 vs 0.985. Full paired intervals and metrics: background_sensitivity.csv/tex.
- acs/lr: reference top-3 changes in 9/10 fixed instances; own-target B8 vs B16 top-3 match 0.935 vs 0.965. Full paired intervals and metrics: background_sensitivity.csv/tex.
- acs/rf: reference top-3 changes in 5/10 fixed instances; own-target B8 vs B16 top-3 match 1.000 vs 0.990. Full paired intervals and metrics: background_sensitivity.csv/tex.
- acs/mlp: reference top-3 changes in 7/10 fixed instances; own-target B8 vs B16 top-3 match 0.930 vs 0.960. Full paired intervals and metrics: background_sensitivity.csv/tex.

## Sample-size illustration, not ACS certification
Bonferroni one-sided Hoeffding over 24 exact antithetic cells: lower=max(0,mean-0.320775). At perfection n=30 reaches at most 0.679225; n>=1235 would be needed for a .95 lower bound at observed perfection under justified sampling assumptions. ACS household PPS-style selection is not justified by the current design.

## Resources

- Main: 27 artifacts; summed CPU 245.296542 s; actual shared cached model rows 125700240; summed cell wall 496.678236 s (not elapsed parallel makespan).
- B16 sensitivity: 6 artifacts; summed CPU 15.243676 s; actual shared cached model rows 614400; summed cell wall 42.442605 s (not elapsed parallel makespan).
Per-cell held-out AUC, log loss, accuracy, fit warnings and resource counters: resources.csv/tex. Logical per-run uncached row costs: logical_costs.csv/tex. Actual timings/rows include the shared references and all methods, not per-explanation deployment cost.

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

## Reproduce / use outputs

```sh
python /work/analyze.py --results /work/results --out /work/analysis
python /work/analysis/plot.py --out /work/analysis
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
