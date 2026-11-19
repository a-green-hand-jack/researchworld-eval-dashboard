# results/ schema

* `raw/<grid>.parquet` — one row per replicate. Columns: `tau` (exact GATE of that replicate's realised potential outcomes),
  estimator columns (`DM`, `REG-L`, `REG-Lc`, `REG-Q`, `REG-G`, `REG-O`, `REG-GBM`, `REG-GCN`, `HT`, `HAJEK`, `HAJEK-r<delta>`, `STAG-*`, `REPEAT-REG`),
  `<REG>_biaspred` (exact finite-d projection bias on that replicate's graph, design-only Monte Carlo, independent seeds),
  `<REG>_L` (corner leverage D' Sigma^-1 D; Var_iid = sigma^2 L / n), `<REG>_se` (network-robust sandwich, closed 2-hop dependence)
  and `<REG>_se_iid`, `HT_var_exact` (exact design variance of HT given the realised potential outcomes; HT is unbiased so this is its MSE),
  graph statistics (`n_eff`, `d_mean`, `d_hm`, `d_med`, `d_cv`, `m_sqrt`=mean 1/sqrt(d)), design statistics (`rho`, `d_eff`, ...), cell parameters (`graph.*`, `out.*`, `design.*`, `tag`, `stag.T`).
  Diagnostics (grid e7): `d1`, `d1q`, `d2`, `d3_B`, `d3_c2`, `d3_se2`, `boot_lo/hi`, `bboot_lo/hi`, `sd_y`, `gscale`.
  C5 analysis (`scripts/analyze_c5.py`, grid e6): `summary/c5_table1.csv` (estimator × mechanism: median and worst over graphs of RMSE/(|β|+|γ|), with CIs), `c5_cells.csv`, `c5_flex.csv` (paired bootstrap against REG-L on the same draws), `c5_best.csv`.
  H4 analysis (`scripts/analyze_c11.py`, grid e11; cell column `obs.q` = fraction of observed-graph edges wrong): `summary/c11_map.csv` (estimator × q × range × response: median/max over graphs of normalised bias, sd, RMSE), `c11_check.csv` (measured vs exact projection bias given the perturbed features).
  C6 analysis (`scripts/analyze_c6.py`): `summary/c6_rank.csv` (Spearman score vs bias/error; `spearman_lo/_hi` for `level == cell`, same bootstrap), `c6_flag.csv` (precision/recall/AUC), `c6_auc_by_mech.csv`, `c6_cover.csv` (coverage, width by regime/mechanism/class, with `*_lo/_hi` 95% bootstrap over cells, 2000 draws, seed 20261119; `class` = inside the curvature rule {linear, concave, convex} / violating it {thresh, convex-2hop} / count), `c6_cover_cells.csv` (per-cell scores and coverage), `c6_B_vs_bias.csv`.
* `summary/<grid>.csv` — one row per (cell, estimator): `bias`, `bias_se`, `sd`, `rmse` with bootstrap 95% CI (`rmse_lo/hi`),
  `n_nan` (undefined replicates), `bias_pred`, `L`, `sd_iid_pred` = sqrt(sigma_tot^2 mean(L/n)), `se_sandwich`, `se_iid`, `cov_sandwich`, `cov_iid` (95% intervals),
  `HT-exact` rows hold sqrt(mean exact HT variance) in `rmse`.
* Normalisation: divide by `|beta|+|gamma|` (=2 in every grid unless `out.beta/gamma` differs), never by |tau|.
* `HAJEK*`: when no unit is exposed in an arm, that arm's mean falls back to the plain arm mean (documented deviation; those replicates behave like DM).
* Replicate unit: synthetic graphs redraw graph + frozen heterogeneity + noise + assignment; `stanford3`, `egofb` fix the graph (`q`<1: fixed thinned copy).
* `summary/c4_bias_pred.csv` (`analyze_c4.py`): one row per (`resp` thresh/concave, `predictor`, e4 cell); `pred` is the held-out prediction (the cell's graph family left out of the fit) of `bias_norm`; also `bias_norm_se`, `d_hm`, `d_mean`. The pooled R² in `c4_bias_loo.csv` is computed from these rows.
* D4 / grid e12 (`analyze_c12.py`): `summary/c12_cells.csv` (per cell: scores (median over replicates), bias and sd of REG-L and of the D4 estimator, flags), `c12_rank.csv` (cell-level Spearman with |bias|, bootstrap CI), `c12_flag.csv` (AUC, flag precision/recall), `c12_estimator.csv` (D4 as an estimator vs REG-L, bootstrap over cells), `c12_by_graph.csv` (medians by graph family and response group). Raw columns `d4` (score), `d4_tau` (corner contrast of the transported fit), `d4_gmax`, `d4_nref`.
