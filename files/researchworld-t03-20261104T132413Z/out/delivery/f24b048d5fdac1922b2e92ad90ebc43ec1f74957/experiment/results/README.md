# Results layout and measure definitions

Everything is produced by `code/` (runs) and `analysis/` (tables) from the raw files; nothing is typed by hand.

| path | content | made by |
| --- | --- | --- |
| `raw/<dataset>__<model>__<stage>.npz` | raw arrays of one (dataset, model) cell; stages `ref`, `kernel`, `perm`, `kernell1`, `retrain`, `bg`, `refcheck` | `code/run_cell.py` |
| `long/runs.parquet` | one row per explainer run: dataset, model, explainer, budget_idx, budget_nominal, rows_evaluated, inst, run, seed, `phi` (list) | `analysis/export_long.py` |
| `long/reference.parquet` | one row per (dataset, model, inst): P(y=1), reference vector `ref`, its SE `ref_se`, `ref_method`, model seed, background size, test AUC | same |
| `long/comparison.parquet` | retrained-model and redrawn-background attribution vectors (`comparison`, `member`) | same |
| `tables/per_instance.csv` | all per-instance measures (cell x explainer x budget x instance) | `analysis/build_tables.py` |
| `tables/cells.csv` | test AUC/accuracy, reference type and its relative SE per cell | same |
| `tables/standards_instance.csv` | comparison standards per instance | same |
| `tables/budget_curve.csv`, `adequacy.csv`, `slopes.csv`, `margin_bins.csv`, `standards.csv` | aggregates with 95% CIs | `analysis/summarize.py` |
| `pilot/` | **pilot-size files (a few instances, few runs); format sample only, not results** | same scripts, small N |

**Resampling unit.** The instance, within a (dataset, model) cell: runs are nested in instances and are never
bootstrapped on their own. Bootstrap CIs are percentile intervals over instances (B=1000, seed 12345); Wilson
intervals for fractions of instances. Cells are never pooled silently. The main model of a cell has one training seed
(0); variation over training seeds appears only in the retrain standard (5 retrains on 80% subsamples, seeds 100-104),
so statements are conditional on that model.

**Definitions** (d attributes; ranking by |attribution|; `phi*` = reference attribution of the same value function).
- Value function: v(S;x) = mean over a fixed background of B=50 training rows of P(y=1 | x_S, b_{~S}) (marginal/interventional);
  features are the original attributes (a one-hot group is masked jointly).
- `rows`: model rows actually evaluated by one explainer call (counted by a wrapper) = budget axis.
- `relerr_mean`: mean over runs of ||phi_run - phi*||_2 / ||phi*||_2. `mse` = mean squared L2 error (for RMS aggregation).
- `match_ref_k{k}`: fraction of runs whose top-k set equals the top-k set of phi*. `jac_ref_k{k}` same with Jaccard.
- `pair_match_k{k}`, `pair_jac_k{k}`: the same for pairs of distinct runs (all R(R-1)/2 pairs): the run-vs-run agreement that needs no reference.
- `nogueira_k{k}`: Nogueira et al. (2018) stability of the R top-k sets (chance-corrected, 1 = identical, 0 = random).
- `kendall_ref`, `rbo_ref`: mean Kendall tau (on signed attributions) / rank-biased overlap (p=0.9, truncated at d and normalised to [0,1], on |.|) between run and phi*.
- `signflip_k{k}`: fraction of the reference's top-k attributes whose sign differs in a run.
- `margin_k{k}` = (|phi*|_(k) - |phi*|_(k+1)) / |phi*|_(1); `gap_sd_k{k}` = sd over runs of the same gap.
- Adequacy at (k, tau): instance is adequate when `match_ref_k{k}` >= tau; the summary is the fraction of adequate instances.
- Standards (`standards*.csv`): `pair_match`/`pair_jac`/`pair_reldist` between members (retrained models, redrawn backgrounds, random other instances),
  the same measure as the run-vs-run one; `null_random_subsets` = chance level for two random k-subsets of d features.

**Notes on budgets.** (i) Permutation SHAP needs `max_evals >= 2d+1` and uses `max_evals // (2d+1)` permutations, so the two smallest ACS-Employment
nominal budgets (40, 64) both give one permutation (786.8 rows): they are replicates of the same setting and appear as two rows with the same `rows`;
they enter the global slope fit as two points and no local slope is computed between them. (ii) Kernel `budget` is the number of coalitions (`nsamples`), `rows` = budget x B + B;
`frac_space` = budget / (2^d - 2): for d<=10 the largest budgets approach full enumeration, so slope fits use only `frac_space <= 0.5`.

**Further tables.** `compute_matched.csv` (C5: repeating a run vs one run with an enlarged budget at equal evaluated rows), `diagnostic.csv` (C4: per-instance
reliability scores `own_margin`, `repeat_z`, `repeat_pmatch` vs the realised flip, AUC with CI), `snr_bins.csv` (top-k match vs gap/noise z-score bins), `timing.csv` (seconds per call).
German (d=20) only: `ref_check.csv` (the converged-Kernel reference against 2^20 enumeration on the first three instances; `ref_vs_exact_rel` vs the stored SE and vs one run's error at the largest
budget) and `l1_default.csv` (Kernel with `l1_reg=False` as in the main grid vs the library default `num_features(10)`, same seeds; `variant=top3_changed_by_default_l1` is the share of runs whose top-3 set differs).
Log-odds sensitivity cells (`<ds>_logit__<model>__*.npz`, same instances and seeds, explained output = log-odds of the clipped probability): `logit_sensitivity.csv` (per explainer, budget and output the same measures against each output's own reference)
and `logit_reference_agreement.csv` (share of instances whose top-k set of phi* is identical for the two outputs). The log-odds cells are not part of the main tables.
Caveat: for logistic regression the log-odds is linear in the standardised features, so Kernel SHAP is exact at every budget (error 0) in that sensitivity cell.

**Tables added for the internal review (`experiment-repo`#7).**
- `c5_hier.csv`: repeat-vs-enlarge for c in {2, 4, 8} pooled over the core cells, one row per explainer x c x subset x metric.  `estimate` is the mean over
  cells of the cell mean over its budget pairs and instances (log error ratio repeat/enlarged: positive = enlarging is better; match difference repeat minus enlarged: negative =
  enlarging is better).  `lo`/`hi`: hierarchical bootstrap (cells, then instances within cells, 2000 resamples); `lo_dataset_cluster`/`hi_dataset_cluster`: datasets first (cells
  of one dataset share instances and random-number streams, see `seed_correlation.csv`), the honest interval when conclusions are about datasets.  `subset=unsaturated` drops Kernel
  pairs whose enlarged budget exceeds half the 2^d-2 coalitions.  Pairs are the budget pairs of the grid whose rows ratio lies in [0.8c, 1.3c]; per-pair rows are in `compute_matched.csv`
  (which now also carries c = 8 and `enl_frac_space`).
- `operating_curve.csv`: a deployer-computable single-run flag.  For each cell x explainer x budget x k: flag an instance when its single-run margin `own_margin` < threshold
  (or the z of n_diag extra runs `repeat_z` < threshold); `false_adequate` = share of really unreliable instances (top-k match probability < 0.9 on the other runs) among the
  unflagged instances, Wilson CI, with `frac_flagged` and `reliable_flagged` (cost of flagging).  `frac_unreliable_overall` is the false-adequate rate when nothing is flagged.
- `snr_bins_cell.csv`: `snr_bins.csv` per cell (pooled over the cell's budgets; instance bootstrap).  Per-cell margin curves are `margin_bins.csv`.
- `retrain_notes.csv`: number of retrain pairs (K(K-1)/2 per instance, not independent: they share the K = 5 retrains) and, for German (d=20), the estimated estimator error of the
  10000-coalition Kernel retrain explanations (an extrapolation of the measured run-to-run variance of the same cell, see the docstring of `analysis/retrain_notes.py`), and the
  share of the retrain-pair variance it contributes.
- `seed_correlation.csv`: Spearman correlation of run noise between two models of the same dataset at the same budget (seeds are the same function of (instance, budget index, run) in
  every cell), with a null in which the run index is permuted.
- `runtime_cells.csv`: wall-clock seconds per stage and cell from `results/logs/`.
- `c5_cell.csv`: the repeat-vs-enlarge comparison per cell (matched-compute pairs), with the sign test over cells in `c5_hier.csv` (`sign_test_p`, `cells_favouring_repeat`).  `c5_hier.csv` has
  `subset` in {all, unsaturated, matched (rows ratio in [0.9, 1.1]), matched_unsaturated, matched_wide ([0.8, 1.25])}; use `matched` for the matched-compute statement.
- `operating_curve_summary.csv`: the operating curve at the margin thresholds that are quoted in the text (false-adequate rate, flagged share, share of reliable instances lost).
- `snr_bins.csv`, `snr_bins_cell.csv`: now with `pred_normal`, the normal-approximation prediction Phi(z) of the match probability in each z bin, next to the measured `match`.
- `ties.csv`: share of tied values at the k-th/(k+1)-th rank of references and of single runs, by budget (needed for the top-k and Nogueira definitions).
- `retrain_sensitivity.csv`: the retrain standard recomputed for subsample fractions 50 %, 80 % (main), 95 % and for a second Kernel seed on the same 80 % retrains (German, d = 20), per cell and k, with instance-cluster CIs, pair counts and mean test AUC.  Only
  (cell, fraction) pairs that were finished when the tables were built appear (see REPRODUCE.md section 6).
- `standards.csv`: the `bg_B50` rows of the d > 12 cells come from a reduced standard (`bgd` stage: 3 redraws of 50 background rows, 30 instances, the explanation recomputed exactly (d <= 16) or by one Kernel run of 10000 coalitions (German)); the d > 12 cells have no `bg_B200` row.
- `ref_check.csv`: the German reference against 2^20 enumeration, on 13 instances for German lr and gbm (first 3 instances plus the `refcheckmore_*` chunks).
- `l1_default.csv`: library-default `l1_reg="num_features(10)"` against `l1_reg=False` for German lr/gbm/mlp and ACS-Employment lr (every cell with a `kernell1` stage).
