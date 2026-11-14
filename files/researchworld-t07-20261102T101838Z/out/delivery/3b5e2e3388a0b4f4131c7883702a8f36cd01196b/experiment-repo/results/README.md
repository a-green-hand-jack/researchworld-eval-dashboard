# results/

Per-prediction tables are the primary output; every metric, CI, figure and table is rebuilt from them (`code/aggregate.py`,
`code/analysis_extra.py`, figtab-repo's `figures/`). Accuracies are fractions in [0,1].

## Per-prediction schema (`predictions/*.parquet`, one row per benchmark x split x seed x n x method x target model)
`benchmark, split_type, s_frac, n_source, n, seed, split_id, method, target_model, true, pred, n_used`
- `true` = mean over **all N items** of the target model (never changed by item filtering); `pred` = predicted full accuracy
  from the target's responses on the `n` selected items only. `n_used` = items actually selected (can be < n for sampling designs that collapse duplicates).
- `split_type`: `random` (25% of models are targets, fresh draw each seed; S fraction 0.75), `extrap` (targets = the strongest 25% by full accuracy;
  deterministic partition, 80% of S subsampled per seed), `family` (leave-family-out fold `seed mod 4`, OpenLLM benchmarks only; S subsampled 80%),
  suffixes mark ablations (`_S10/_S20/_S40`: only that many source models; `_T50`: 50% targets; `_nodedup`: exact duplicate model rows kept; `_fact`: selector x estimator grid),
  `_inner` = source-internal design-freezing runs (`results/freeze/`).
- `seed` = repetition index (selector seeds, S subsampling, and for `random` the S/T draw). For deterministic splits it is *not* a split seed.

## Methods (column `method` = `selector+estimator`)
| name | role | meaning |
|---|---|---|
| `const` | B0 | predict the mean source accuracy; ignores the target's outcomes |
| `random+mean` | B1 | uniform random subset, subset mean (unbiased) |
| `strat+mean` | B2 | one random item per stratum of source-difficulty-sorted items, subset mean |
| `random+cal` | B3 | B1 recalibrated by a 1-D linear regression subset-mean -> full accuracy fitted on source models |
| `anchor+anchor` | existing | Anchor Points: KMeans on a 16-d SVD embedding of item response vectors (sources), medoid per cluster, weights = cluster sizes |
| `anchor+irt` | existing (tinyBenchmarks-style) | anchor items + 4-d 2PL IRT ability (MAP) -> mean predicted probability; no gp-IRT mixing |
| `random+irt` | existing | random items + the same IRT predictor |
| `random+lowrank` | existing-style MF | random items + rank-8 PCA/MAP latent-factor imputation of the target row |
| `omp+ridge` | P1 (supervised selection) | greedy orthogonal-matching-pursuit item selection on sources, ridge regression subset responses -> full accuracy |
| `strat+lowrank_dr` | **P3 (frozen proposal)** | stratified sample + low-rank prediction + Hajek-weighted mean residual correction (difference estimator) |
| `strat+lowrank_eb` | P3 variant | as P3 with the correction shrunk by g = r^2/(r^2+Var(r)) |
| `strat+lowrank`, `random+lowrank_dr` | ablations of P3 | selection only / estimator only |
Factorial runs (`_fact`) use further selectors (`pps`, `omp`, `copt`) and estimators (`ridge`, `knn`, `irt_dr`, `ht`), see `code/bpx/methods.py`.

## Derived tables (`tables/`, made by `code/aggregate.py` and `code/analysis_extra.py`)
`metrics_by_seed.csv`, `summary.csv` (mean over seeds, percentile bootstrap 95% CI over seeds, B=1000), `paired_vs_baseline.csv`
(difference to B1 within the same benchmark/split/n/seed, CI by bootstrap over seeds; `*_win_rate` = share of seeds with improvement),
`rank_summary.csv` (mean rank across benchmarks, descriptive only), `q4_bias_variance.csv`, `q4_by_true_tercile.csv`, `q6_pairwise_by_gap.csv`, `sanity/`.
