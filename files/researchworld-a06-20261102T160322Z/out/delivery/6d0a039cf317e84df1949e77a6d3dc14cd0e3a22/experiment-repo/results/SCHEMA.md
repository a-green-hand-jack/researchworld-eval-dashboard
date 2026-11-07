# Result-file schema (deviations from the figtab request in `experiment-repo#3` are listed first)

Deviations: files are named `<what>_<tier>.parquet|csv` (`runs_t0`, `methods_t0`, `decisions_t0`, `decisions_ab_t0`, `theory_curve_t0`, `summary_*_t0`; `*_t1` for the real arm); parquet for the two replicate-level files (CSV would be >300 MB).
No `t2_live` file: no live-tool run was made (see REPRODUCE.md). Leakage cells are rows with `leakage=1` (and `|leak=1` in `cell_id`).
Every replicate is a row; nothing in `runs`/`methods` is pre-aggregated.

## runs_<tier>.parquet — one row per search replicate
`tier, cell_id, rep, seed` (base seed; per-replicate stream = (seed, crc32(cell_id), rep)), `n` (|D|), `K` (candidates in the space), `K_eval` (candidates actually evaluated by the procedure),
`tau` (T0: SD of config effects on the probit scale; T1: NaN), `rho` (T0: latent correlation of config×item effects across configs; T1: NaN), `base_acc` (T0: baseline accuracy; T1: baseline config accuracy on the pool),
`procedure` (`exhaustive` | `halving` | `greedy`), `leakage` (0/1: few-shot demos drawn from D), `subject` (`all`), `n_fresh`, `theta_se` (T0: 0; T1: binomial SE of θ(ĉ) on the fresh set),
`chosen_config`, `reported_naive` (M0, accuracy of ĉ on D), `theta` (accuracy of ĉ on fresh items: exact population value in T0), `theta_pop_mean` (mean θ over the K candidates),
`theta_best` (max θ over candidates), `theta_base` (θ of the baseline config), `baseline_reported` (baseline config's accuracy on D), `tuned_untuned_fresh_gain` (θ(ĉ) − θ(baseline)).
Gap Δ = `reported_naive − theta`.

## methods_<tier>.parquet — one row per (replicate, method)
`tier, cell_id, rep, n, K, tau, rho, base_acc, procedure, leakage` + `method`, `estimate`, `lo`, `hi`, `level` (0.95 nominal; NaN when the method gives no interval), `items_search`, `items_report` (item cost: items consumed by search / by the report),
`target` (`theta_chat` = θ of the selected config; `E_theta_procedure` for M2 = mean θ of the fold-selected configs),
`theta_target` (the truth the method is scored against: for M1_f*, θ of the config selected on the search part of D, which can differ from the final `theta_chat`; for M2 the mean θ of the fold-selected configs; otherwise θ(ĉ)), `theta_chat` (θ of the final ĉ), `base_est` (the same method's estimate for the fixed baseline config, for decision rules), `theta_base`. (`calib_split` is an unused, empty column.)
Methods: `M0`; `M1_f0.2/0.5/0.8` (hold-out, fraction of D kept for selection); `M2` (5-fold cross-fitting); `M3_opt`, `M3_632` (Efron optimism / .632, subset of cells, `|m3` in `cell_id`);
`M4_simult` (simultaneous multiplier-bootstrap lower/upper bounds over all K), `M4_cond` (conditional polyhedral interval + median-unbiased estimate, argmax selection only), `M4_hybrid` (hybrid conditional/projection interval, argmax only);
`M5_eb` (empirical-Bayes shrinkage of disclosed scores, with posterior interval), `M5_ladder` (Blum–Hardt ladder over the K evaluations in random order, step η=n^(−1/3); reports a rounded best-so-far value, no interval), `M5_ladder_se` (ladder with step η=0.5/√n).

## decisions_<tier>.csv, decisions_ab_<tier>.csv — one row per (cell, method, regime, rule variant)
`tier, cell_id, n, K, tau, procedure, method, regime` (true-gain regime: `gain<=0`, `gain>0` for margin 0; `gain<=0`, `0<gain<m`, `gain>=m` for margin 0.02), `n_reps`, `n_reject` (claim made),
`rule` (`tuned_gt_baseline_by_m`; `A_gt_B` for the pair file, which adds `cell_A, cell_B`), `variant` (`point`: estimate − base_est > m; `lo`: lower bound − base_est > m, only rows with a bound), `margin_m` (0 or 0.02).
Regime cells with few replicates exist (false-claim regimes are rare at large tau); use `n_reps` and Wilson intervals, pool regimes that are not a true claim.

## summary_gap_<tier>.csv, summary_methods_<tier>.csv — aggregates (convenience; recomputable from the replicate files)
Gap: mean/sd/quantiles of Δ per cell, `gap_mcse = sd/√reps`. Methods: `bias` (estimate − theta_target), `bias_mcse`, `rmse`, `coverage` with Wilson `cov_lo/cov_hi`, `width_median`, `frac_infinite_width`, `frac_estimate_missing`.

## theory_curve_t0.csv
`gap_theory` = s²·g(K)/√(τ_p² + s²) for exhaustive search with `s² = σ²(1−r)/n`, `σ² = θ0(1−θ0)`, `r` the binary correlation of two configs implied by `rho` and `base_acc`
(`t0.binary_corr`), `τ_p = tau·φ(Φ⁻¹(base_acc))` (config-effect SD on the probability scale), `g(K) = E[max of K standard normals]`; `gap_measured` and `gap_mcse` from the simulation. Leakage cells excluded.

## cost files
`results/t0*/shard*.cost.csv`: wall seconds and replicates per cell. `results/compute.csv`: compute per job (see MANIFEST.md).


## T1 (real LLM, `*_t1*`)
Same columns as T0 with: `tier=T1`, `tau`/`rho` NaN, `block` (0..9: replicate `r` draws D and the fresh set F from the pool without block `r % 10`, "delete-a-block" for SEs), `n_fresh` (|F| = 1 800 − n: pool items in neither D nor the left-out block of 200, i.e. 1 300-1 750), `theta` = accuracy of ĉ on F (a finite-sample value; its binomial SE is `theta_se`), `chosen_name` (prompt-config name or `ens(a+b)` pair ensemble). Candidate index 0 is always the baseline config `terse|is|0shot` (pool accuracy 0.227); `K=24` = the 24 base configs, other K = baseline + K-1 random draws from the 300 candidates (24 base + 276 pairwise logit-average ensembles). Cells `|m3` repeat the exhaustive K=24/300 cells at n=100, 500 with M3 (B=100) on.
* `summary_gap_t1.csv`: as T0, plus `gap_block_se` (SD of the 10 block means / sqrt(10); a replicate-overlap-robust SE, use it for T1 uncertainty rather than `gap_mcse`) and `gap_theory_from_matrix` (closed form fed with the matrix's own sigma, r, tau; exhaustive cells only).
* `t1_matrix_summary.csv`: per-config pool accuracy (+ binomial SE) and, for the base-24 and all-300 candidate sets, the empirical analogues of the T0 parameters (`sigma, r_binary, tau_prob_est`, accuracy range).
* `subject_breakdown.csv`: gap of the selected config per MMLU-Pro subject (exhaustive, K=24 and 300, n=50..500): `mean_gap`, `sd_gap`, `mcse`, mean search/fresh items in the subject (a subject has only ~3-25 search items at n=100-500, ~1-10 at n=50, so single-replicate subject gaps are very noisy; interpret the replicate mean with its `mcse`).
* `t0_vs_t1_gap.csv`: T1 gap vs the T0 cells with the same (n, K), base_acc 0.3, tau in {0.05, 0.1}; T0 columns `t0_*`, `t0_over_t1` ratio. T0's parameters are not calibrated to the matrix: this table compares gaps, the calibrated test is `gap_theory_from_matrix`.
* Pair design (`*_t1_pairs*`, `decisions_ab_t1.csv`, `summary_pairs_t1.csv`): A and B are tuned (exhaustive) on the same D from disjoint candidate subsets of sizes K_A, K_B; cell ids `pair|n=N|KA=..|KB=..|A|B`. `decisions_ab_t1.csv` has the columns of `decisions_ab_t0.csv` (`regime`: `A_not_better`/`0<gain<m`/`gain>=m` by the fresh-set difference) plus `n, K_A, K_B`. `summary_pairs_t1.csv`: mean reported and true difference, `p_true_A_better`, `p_reported_A_better` (strict >), `p_rank_flip` = share of replicates with sign(reported diff) != sign(true diff), a tie in reported scores counting as a flip. Because A and B are drawn from the same family with a small config spread, the true difference is mostly tiny; the false-claim regimes are therefore well populated here.
* Decisions in T1 (`decisions_t1.csv`): the baseline is a weak config, so nearly all replicates are in the true-gain regime `gain>=m`: false-claim rates against it cannot be estimated from T1 (regime rows with `n_reps` < 30 should not be used); use the pair design for false-claim and flip rates.
