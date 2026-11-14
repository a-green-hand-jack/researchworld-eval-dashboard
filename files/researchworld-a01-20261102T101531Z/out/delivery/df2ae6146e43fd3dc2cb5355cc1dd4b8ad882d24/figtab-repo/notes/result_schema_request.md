# Result tables the figures/tables need (request to experiment-repo)

Tidy CSV (UTF-8, header row, no index), one file per table, under `results/` in experiment-repo. Column names exactly as below;
extra columns are fine. Every file should be accompanied by the script and the commit/data sha that produced it.

Common key columns (any table): `leaderboard` (`openllm_v2`|`helm_mmlu`), `granularity` (`headline`|`subtask`), `rule`
(e.g. `mean`,`median`,`trimmed_mean`,`geomean`,`min`,`power_mean`,`borda`,`win_rate`,`plurality`,`copeland`,...),
`rule_param` (p for power mean / trim fraction; empty otherwise), `gain_model` (`G1`..`G4` + parameter, e.g. `G2_0.5`),
`cost` (`linear`|`convex`), `field` (`all`|`top50`|`top10`), `tie_break`, `spillover_rho`, `noise_margin` (0 = none).

1. `per_target.csv` - one row per (key columns, target): `target_id`, `init_rank` (under that rule, in that field),
   `incumbent_gap` (in the rule's score units where defined), `n_tasks`, `k_min` (int; empty if infeasible), `G_min`
   (float; empty if infeasible), `feasible` (0/1), `exact` (1 = exact solution, 0 = heuristic/upper bound),
   `p_first_noise` (optional: Monte-Carlo probability of ranking first after the investment, when a noise margin is used).
2. `paired_stats.csv` - one row per planned contrast (e.g. mean vs median, over targets feasible under both): key columns of
   both arms, `contrast`, `metric` (`k_min`|`G_min`|`feasible`), `n_pairs`, `estimate` (median paired difference and/or
   ratio, say which in `estimate_type`), `ci_lo`, `ci_hi` (bootstrap over models; state resamples + seed in `ci_method`),
   `n_counterexamples` (pairs where the claim's direction is reversed).
3. `feasibility.csv` - may be derived from (1) but please supply: key columns, `rank_bin` (`1-2`,`3-10`,`11-100`,`rest`),
   `n_targets`, `frac_feasible`, `ci_lo`, `ci_hi` (Wilson or bootstrap; say which).
4. `subsample_curves.csv` - task subsampling for C5: key columns, `n_tasks`, `rep` (subsample index, seed in column `seed`),
   then per rep summary: `median_k_min`, `median_k_min_frac` (k_min/n), `median_G_min`, `frac_feasible`. If you bootstrap
   the curve instead, supply `*_lo/_hi` columns and say so.
5. `power_mean_curve.csv` (C3) - key columns with `rule=power_mean`, `p` over a grid including -inf (min), 0 (geomean), 1
   (mean), +large; `median_k_min`, `ci_lo`, `ci_hi`, `frac_feasible`; plus rows for borda / win_rate / median for the same
   targets so they can be placed against the curve.
6. `verification.csv` (C1) - one row per (leaderboard, granularity, gain_model, target) or per aggregated check: `formula_value`,
   `search_value`, `abs_diff`, `match` (0/1), and `instance_type` (`real`|`small_exhaustive`) for the heuristic-vs-exhaustive
   checks of rank-based rules.
7. `ablation.csv` (C6) - one row per (factor, level, rule): `factor` (gain_model|granularity|field|tie_break|noise|spillover|
   normalisation|leaderboard), `level`, `rule`, `metric`, `estimate`, `ci_lo`, `ci_hi`, `n_targets`, and
   `claim_holds` (0/1 for the direction of C2/C3/C4 under that cell, with the criterion in the README).
8. `data_manifest.json` - for the Data table: per source: url/snapshot sha, date, sha256 of files used, #models before/after
   exclusions, #tasks, exclusion counts by reason.

Units: scores 0-100 points; `G_min` in points, `k_min` in tasks. Please keep infeasible targets in the tables (empty value
+ `feasible=0`), because the figures show them as a separate outcome, not drop them.
Scripts for figures will live in figtab-repo `code/` and read these files from experiment-repo's results path.
