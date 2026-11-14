# results/ schema

Raw runs: `results/<dataset>/raw/<model>/<cell>_r<rr>.npz` (`phi` [N,d] attributions of run `rr`, explainer seed 10000+rr,
`seconds`, `nsamples`, `evals`); targets: `results/<dataset>/targets/<model>.npz`; `instances.json` (positions in the
held-out test split; `stratum` random|near_boundary, interleaved so that any prefix is balanced); `models.json`.
Tidy tables (all produced by `python code/analyze.py`; bootstrap seed 2024, `n_boot` in each file) in `results/tidy/`:

| file | one row per | key columns |
|---|---|---|
| `runs_metrics.csv` | (dataset, model, cell, instance, metric) | `value` = metric averaged over the R runs (pairwise metrics: over all R(R-1)/2 pairs); `stratum` |
| `summary_ci.csv` | (dataset, model, cell, metric, stat) | `est, lo, hi` (nested bootstrap 95%: instances, then runs within instance), `n_instances, R, n_boot, seed`; rows with `cell=null_perm` are the permuted-feature chance level |
| `gap_to_noise.csv` | (cell, instance, pair_rank j) | `gap` = \|t_(j)\|-\|t_(j+1)\| of the target, `sd_diff` = SD over runs of the same difference in \|phi\|, `ratio`, `p_order_reproduced` |
| `verdicts.csv` | (dataset, model, cell) | pre-stated decision rule (PLAN §0) applied to the bootstrap bounds |
| `contrasts.csv` | planned paired contrast x metric | `mean_diff_A_minus_B`, bootstrap CI, Wilcoxon p, Holm-adjusted p (within metric) |
| `equal_budget.csv` | (dataset, model, comparison, metric) | one run at B vs mean of g runs at B/g (equal total evaluations) |
| `budget_levels.csv` | (dataset, model, cell) | `nsamples`, `background`, `budget_evals`=nsamples x K, measured `sec_per_explanation_mean`, `us_per_model_eval` |
| `models.csv` | (dataset, model) | value function, test AUC/accuracy, n_train/test, d, parameters |
| `cells_not_run.csv` | planned cell without runs | reason |

Columns shared by the cell tables: `cell` (kernel_q = 0.25x, kernel_1 = 1x, kernel_4 = 4x, kernel_16 = 16x the library
default nsamples 2d+2048, all with `l1_reg=False` (arm `l1_off`); `kernel_1_l1default` = shap 0.51 default
`l1_reg='num_features(10)'` (arm `shap_default_l1`); `perm_1`, `perm_4` = shap PermutationExplainer at 1x/4x
of the same nsamples), `explainer` (kernel|perm|null_perm), `level_x_default`, `budget_evals`, `target` (how the
exact reference was computed: enumeration | closed_form | treeshap | none).

Metrics (higher = more reliable unless the name ends in `_dist`/`_err`): pairwise between two runs
(`spearman_abs`, `top{1,3,5}_jaccard`, `rbo` (p=0.9, extrapolated), `sign_top3`, `rel_l2_pair_dist`) and against the target
(`rel_l2_err`, `max_abs_err_over_scale`, `spearman_abs_target`, `top{1,3,5}_hit`, `top3_exact_order`,
`sign_top3_target`, `sign_all_target`). Rankings are by |phi|.
