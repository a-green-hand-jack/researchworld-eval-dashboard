# figdata: result files for figures and tables (schema: figtab-repo/schema.md)

Produced by `python exp/export_figtab.py` (producing commit stated in `PROVENANCE`, rewritten at each export) from the raw
records in `results/`. Re-running overwrites these files; a file that is absent has not been computed yet.

Conventions (all files)
* Metrics are in standardised units (per-benchmark z-score from history-model statistics only), RMSE = sqrt of the mean of squared errors over a
  model's unobserved (held-out) benchmarks; pair_acc = pairwise accuracy of "which history models does the new model beat" on the unobserved
  benchmarks; top10 = F1 of top-10-history-model inclusion; spearman = per-model rank correlation over unobserved benchmarks.
* CI = 95% percentile bootstrap (B=2000) over held-out models (the unit of replication); metrics are first averaged over repeated cross-fits per model.
  For forecasts and E6 / synthetic / sweep cells the bootstrap unit is the cross-fit unit (rep x fold; split block; synthetic replicate) and is stated per file.
* `random` selector: >=100 random draws (30 on OLMB40), averaged per model; decision metrics (pair_acc, top10, spearman) of `random` use the first 10 draws
  (5 in group/cost runs) -> `n_draws` is the RMSE draw count.
* matrices: A1 (103x202 complete MTEB block), A2 (126x30), B (sparse 507x598, 22% observed, availability-constrained), OLMB40 (Open LLM Leaderboard v2 subtasks, 4508x40),
  OLMB6, HELMMMLU (79x57), HELMLITE (91x10), LIVEBENCH (195x7, 23% missing). MTEB splits are random cross-fits over models; the LLM matrices use family/organisation-held-out folds (`split=family`).
* `selector`: greedyA (A-optimal on the latent factors; the core criterion), greedyAcomp (expected error on the complement), greedyD, greedyGauss (rank-free, shrunk-covariance conditioning),
  greedyAT (target-aware A), greedyAcost / greedyGaussCost (gain per unit cost), random, covered, central, cluster (k-medoids), pivqr, leverage, fwdreg.
  `inference`: fa (latent factors, rank by held-out likelihood), fa_pcv (rank by predictive CV), gcov, mean, meanz, ridge, knn, softimpute.
* references.csv kinds: `forecast` (finite-M-corrected closed-form prediction of RMSE(k) for the greedyAcomp+fa selection from the history fit only), `forecast_noinfl`, `forecast_naive` (plug-in of formula (a)),
  `lower_bound` (tail bound sum_{i>k} lambda_i, sanity floor), `empirical_floor` (RMSE of predicting each benchmark from ALL other observed benchmarks of the same model; constant in k), `mean_predictor`.
  The forecast rows refer to selector greedyAcomp + inference fa curves in curves.csv.
* paired.csv: `diff` is a - b (negative = first named is better) in mean squared standardised error (`mse`) or relative to the baseline mean (`rel_mse`);
  family `primary` = the Holm-corrected family declared in PRIMARY_COMPARISONS.md ("[post-pilot]" marks P7/P8); `exploratory` = BH over the exploratory family within each matrix.
* Extra columns beyond the schema (all documented here): shift.csv `selector, inference, coverage_conformal, coverage_lo/hi, rmse_meanpred, pred_rmse, n_units`; kstar.csv `selector, inference,
  kstar_truth, mean_signed_log2_ratio_vs_truth, frac_censored, n_units`; cost.csv `selector_class, selector, inference, budget_frac`; references.csv extra kinds.
* kstar.csv: k censored at 60 (real) / 21 (synthetic) when never reached; rules: model (predicted RMSE <= tol), conformal (calibration-model mean RMSE <= tol), conformal_q (90% quantile), empirical (measured),
  oracle (true-parameter formula; synthetic only).
* synthetic_grid.csv: N=48 benchmarks, unit-variance, `latent_var_frac` h = latent share of variance, snr = h/(1-h) (levels h=0.3/0.6/0.9); `forecast` in {oracle (true parameters, formula (a)), naive (plug-in of the fit), fm (finite-M corrected), fm_noinfl}; `measured_rmse` is the held-out error of the selection+FA
  fitted on M history rows (20 replicates; CI bootstrap over replicates); the relative gap |predicted-measured|/measured at the 10% tolerance is computable per row. Selector greedyAcomp; plug-in rank by held-out likelihood.
* h3_selector_x_inference.csv (F6 cross): held-out `mse` (standardised, mean over models; CI bootstrap over held-out models, per-model values averaged over 5 repetitions and 20 random draws) for selector in {greedyAcomp, random} x inference in {fa, extratrees, kernelridge},
  matrices A1, A2, HELMMMLU, k = 3, 8, 12 (+ 20, 30 where H3k is finished: A2 20 only, N = 30). h3_selector_x_inference_paired.csv: `diff` = greedyAcomp - random in mse, `rel` = diff / mean(random), `lo/hi` = 95% CI of diff, `p_adj` = Holm over that file's rows (family H3r, not part of P1-P8).
  h3_imputers_paired.csv: FA vs ExtraTrees / kernel ridge / mixture of FAs and adaptive vs nonadaptive (family H3, Holm over all 54 rows; `diff` = first - second, positive `rel` = first named (FA) worse). ExtraTrees and kernel ridge give point predictions only: no model-based predictive variance and no forecast of error vs k (not in kstar.csv/shift.csv).
* kstar.csv, censoring on the LLM matrices: the 60 (real) is a cap, not a grid point. The k grid of E6 ends at 30 on OLMB40, at 5 on OLMB6 (N = 6) and at N-1 on HELMLITE/LIVEBENCH, so `frac_censored` > 0 means the tolerance was not reached on that grid; OLMB6 has only k <= 5 and its stopping-rule rows are not informative about k* (use shift.csv coverage for it).

## Real-matrix conditions for F4 (`real_conditions.csv`, extra `kstar.csv` rows)
- `real_conditions.csv`: per matrix, median (min, max) over all stored fold fits of the FA latent share of variance
  `latent_var_frac` = sum(Lam^2) / (sum(Lam^2) + sum(psi)) on history-standardised columns (same definition as `latent_var_frac` in
  `synthetic_grid.csv`), and the fitted rank `fa_rank` (columns of Lam; rank chosen by the protocol's CV per fit). LLM-matrix rows come from
  the E7 fits on disk and are preliminary until the E7 reruns finish.
- `kstar.csv` rows with `metric = rmse_over_meanpred` and `spectrum` empty are the real matrices on the synthetic axis (tol 0.5, 0.7),
  selector greedyAcomp, inference FA. `empirical`: first grid k with sqrt(mean MSE(FA) / mean MSE(history-mean predictor)) <= tol; `model`: the
  same with the finite-M forecast in the numerator (A1/A2 only). `frac_censored` is 1 when the tolerance is not reached on the k grid (`kstar` = grid max + 1),
  else 0; it is a property of the pooled curve, not a per-unit fraction. k* is a grid point (grids: 1-6, 8, 10, 12, 15, 20, 30...).

## E2 files (group transfer and cost; F3)
- `group_paired.csv`, `cost_paired.csv`: the paired tests of results/E2 unchanged (families G1/G2 and P4; `diff` = first named - second in standardised MSE, negative = first better; `rel` = diff / mean of the second; Holm over the family, columns `p_adj` / `p_holm`; `explor` rows are not Holm-corrected).
- `cost.csv`, note on reading: the k grid ends at k = 80 (A1) and k = 20 (A2), which is only 1.7% (A1) and 7% (A2) of the total cost of all benchmarks. Budget fractions in cost.csv above the cost of the largest grid k are evaluated with that largest k (no larger set was fitted), so
  flat cost-aware curves at large budgets mean "the grid ended", not "no gain from a larger budget".

## Setting B (`primary_B.csv`)
`primary_B.csv` = `results/B/primary.csv` (columns as `results/A1/primary.csv`: `test, k, diff, lo, hi, p, rel, n_models, post_pilot, p_holm`). Holm family = 33 tests (11 comparisons x k in {3, 8, 20}); P2 (greedyA vs covered) is no longer repeated
under P3 (the earlier 36-row file counted it twice). The declared family also names cluster and leverage; on B they were not run (cost: 30 min per fold with 598 benchmarks), so they are not in the family and the correction
is over the comparisons that exist. Setting B is final: 3 repetitions x 5 folds (15 fits); the per-model errors are averaged over repetitions before the paired bootstrap over the 354 held-out models. Compared with the one-repetition version, 3 signs and 7 Holm outcomes changed (see experiment-repo#4, item 5).
