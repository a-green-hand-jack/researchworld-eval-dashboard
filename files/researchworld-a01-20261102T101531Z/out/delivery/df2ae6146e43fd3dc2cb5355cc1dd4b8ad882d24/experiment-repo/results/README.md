# results/ — tables produced by `code/analysis` (schema of figtab-repo `notes/result_schema_request.md`)

All tables are tidy CSV, scores in points (0–100), `k_min` in tasks, `G_min` in points. Infeasible targets are kept
(`feasible=0`, empty `k_min`/`G_min`). Script → table map and commands: `REPRODUCE.md`.

## Model and definitions (the conventions every table uses)

* **Attack.** Target model *t* chooses a set *T* of tasks and raises its score on each task *j* ∈ *T* by at most
  *u_j* = min(δ_j, hi_j − s_tj)⁺; every other score on the board is unchanged. All rules are monotone in the target's own scores,
  so using the full boost on the chosen tasks is optimal and the problem is *which* tasks (k_min) or *how many points* (G_min).
  "First" = **strictly** first (a tie is not first; `tie_break=strict`, the tie-break variant was not run).
* **Gain models (`gain_model`).** `G1`: δ = ∞ and cap hi_j = (best score on task *j* over the whole board) + 1.
  `G1_add10`/`G1_add20`: at most +10/+20 points, same cap. `G2_γ` (γ ∈ {0.25, 0.5, 1}): δ_j = γ·(hi_j − s_tj), same cap
  (`G2_1` ≡ `G1` by construction; both are kept so the grid is complete). `ceil`, `ceil_add10`, `ceil_add20`: as G1 / G1_add10 / G1_add20 but cap 100.
  G4 (calibration from fine-tune/base pairs) was cut, as planned (`PLAN.md` §6).
* **Cost (`cost`).** `linear`: G = Σ x_j points. `headroom`: Σ x_j/h_j with h_j = hi_j − s_tj (share of headroom closed). `k_min` does not depend on the cost.
* **Rules (`rule`, `rule_param`).** `mean`; `geomean` (geometric mean of s+1, param 0); `median`; `min`; `trimmed_mean` (param 0.2 = 20% cut per side);
  `power_mean` (power mean of s+1, param p ∈ {−2, −1, 0.5, 2, 4, 8}; min = p→−∞, geomean = p=0, mean = p=1);
  `borda` (mean rank; identical ranking to the HELM mean win rate); `copeland`; `plurality` (number of first places); `condorcet_winner` (target must beat every rival by pairwise majority).
* **Exactness (`exact`, `G_min_kind`).** `exact=1`: `k_min` is the exact optimum (closed form / sort / water-filling for the cardinal rules,
  subset enumeration for n ≤ 10, a multi-cover 0/1 MILP (HiGHS) for Borda/plurality/Copeland/Condorcet at n > 10, validated against brute force: `verification.csv`).
  `exact=0`: `trimmed_mean` with n > 10 (greedy + prune, an upper bound on k_min); in `per_target.csv` rows whose point cost is only a frontier upper bound (below) also carry `exact=0` although their `k_min` is exact — use `headline.csv:k_min_exact` or the rule to tell the two apart. `G_min_kind`: `exact` (mean, geomean, p<1 power means, min, median with odd n; fractional knapsack /
  water-filling), `upper_bound_frontier` (borda, plurality, copeland, condorcet, trimmed mean under G1 and linear cost only: min over k of k·Δ*(k) from the Δ*-frontier on a grid of k, so a valid but loose bound; `exact=0`), `na` (not computed).
* **Targets.** HELM: all 79 models. OLB headline: the 30 top models by mean plus 300 log-spaced ranks (209 distinct models) — a rank-stratified sample, **not** a uniform sample of the 4,496 models;
  paired statistics are therefore reported per rank stratum. OLB sub-task: same rule on a 699-model pool. `init_rank` is the rank under the row's own rule within the field; `rank_mean` (a column of `per_target.csv` and `per_target_ablation.csv`) the rank under the mean.
* **Populations (`population`).** HELM `all` (79 complete models). OLB `no_flagged` (default: unflagged, one row per fullname, best Average; 4,496), `all` (4,576), `no_merges` (2,676), `official_providers` (450);
  `subtask_pool_699` for the sub-task level. `normalisation`: `normalised` (the leaderboard's own columns) or `raw`. `field`: `all`, `top50`, `top10` (leaderboard restricted to the top-N by mean plus the target).
* **Not run:** `tie_break` other than `strict`, `spillover_rho` other than 0 (columns present for the schema, constant).

## Tables

| file | content | made by |
|---|---|---|
| `per_target.csv` | one row per (rule, rule_param, gain_model, cost, target) in the four main specs: `helm_mmlu` headline; `openllm_v2` headline (normalised and raw); `openllm_v2` sub-task. Columns: `target_id, init_rank, incumbent_gap, n_tasks, n_models, k_min, G_min, G_min_kind, feasible, exact, p_first_noise (empty here), rank_mean` + key columns | `09_per_target.py`, `11_collect.py` |
| `headline.csv` | the one-place answer for the main text: leaderboard/level × gain model (`G2_0.5`, `G1_add10`, `ceil_add10` = bounded gains where feasibility is non-trivial; `G1` = unbounded reference) × rule × rank stratum by mean-rank (`2-10`, `11-100`, `101+`, `all_attackers`) → `frac_feasible` (Wilson CI), `median_k_min`, `median_G_min` over the feasible targets (percentile bootstrap CI over targets, B=2000, seed 20261104; IQR), `G_min_kind` (`exact` / `upper_bound_frontier`; the median `G_min` is left empty where it is defined for < 90% of the feasible targets, e.g. ordinal rules outside G1, even n), `k_min_exact` (0 only for the trimmed mean at n > 10). Linear cost, normalised scores. Medians are conditional on feasibility: read them together with `frac_feasible` | `16_headline.py` |
| `per_target_ablation.csv` | same schema for the C6 cells: OLB populations (`all`, `no_merges`, `official_providers`), fields `top50`/`top10` on both boards; core rules, gains `G1, G2_0.5, G1_add10, ceil`, linear cost | `09_per_target.py ablation_*` |
| `per_target_noise.csv` | noise rows: `noise_margin` is the required probability of ranking first (0 = none; then `p_first_noise` is the probability at the noise-free `k_min`); `k_min` = smallest k reaching that probability (empty = not reached up to n or the extension grid) | `13_noise_robust.py`, `11_collect.py` |
| `paired_stats.csv` | contrasts `mean vs <rule>` per cell and rank stratum; metrics `k_min`, `G_min` (both exact), `feasible`; `estimate_type` = `median_diff(other-mean)` or `median_ratio(other/mean)` (pairs with k_mean>0); `n_counterexamples` = pairs where the other rule needs *less* than the mean (claim C2 reversed), `n_ties`, `n_only_one_feasible`. CI: percentile bootstrap over target models, 2,000 resamples, seed 20261104 | `11_collect.py` |
| `feasibility.csv` | `rank_bin` (1-2, 3-10, 11-100, rest) × key columns; `rank_basis` = `rule` (rank under the row's rule) or `mean`; `frac_feasible` with Wilson 95% interval | `11_collect.py` |
| `power_mean_curve.csv` | C3: `median_k_min` along p ∈ {−inf, −2, −1, 0, 0.5, 1, 2, 4, 8} (`family=1`) with bootstrap CI over targets, plus median/borda/copeland/trimmed/plurality/condorcet rows (`family=0`) for the same targets; per rank stratum. p = +inf (max) was not run: 8 is the largest p | `11_collect.py` |
| `power_mean_monotonicity.csv` | share of targets whose `k_min` is monotone in p (either / each direction), mean Kendall τ | `11_collect.py` |
| `subsample_curves.csv`, `subsample_curves_summary.csv` | C5: random task subsets (20 per n; seed 20261103), sub-board targets at mean-rank 2/5/10/20; per-rep medians (`target_rank` = single rank or `2-20 (median of 4)`) and the mean/2.5–97.5% range over reps | `12_subsample.py` |
| `baselines.csv`, `baselines_budget_needed.csv` | share of targets that are first with budget k (tasks) or G (points) under `optimal`, `greedy_headroom` (tasks with the largest headroom), `random` (100 draws per target), `uniform` (G/n on every task, mean and geomean); `median_budget_needed` | `10_baselines.py`, `11_collect.py` |
| `verification.csv` | C1: `instance_type=real` — mean-rule closed form (G_min = n·gap; k_min = smallest k with the k largest boosts exceeding n·gap) vs the solver, plus an independent check with the reference rule (`applied_check`); `small_exhaustive` — solver (closed-form/MILP path forced) vs brute force over all task subsets for every rule on 400 random small instances with ties | `14_verification.py` |
| `ablation.csv` | C6: one row per (factor, level, rule, metric); metrics `C2_median_diff_k(other-mean)`, `C4_spearman(rank_mean,feasible)`, `C3_frac_monotone_in_p(either direction)`; `claim_holds` ∈ {0,1} with the criterion in `claim_criterion`; `claim_in_plan` = 1 for the rules the plan names (median, borda, copeland, condorcet) | `11_collect.py` |
| `data_manifest.json` (copy: `../data/manifest.json`) | sources, snapshot ids, SHA-256 of every file used, model/task counts, exclusion counts | `15_manifest.py` |
| `noise_robust.csv`, `noise_robust_{helm,olb}.csv` | k reaching P(first)≥0.5/0.9 under item-level evaluation noise (Gaussian approximation of the binomial error) | `13_noise_robust.py` |
| `mink_*.csv`, `frontier_*.csv`, `l1_cost.csv`, `noise_{helm,olb}.csv`, `synthetic.csv`, `tab_*.csv` | earlier exploratory grids (Δ-grid min-k, Δ*(k) frontier, L1 costs, Monte-Carlo ranks under noise, one-factor synthetic boards, summaries); inputs of the appendix and of the frontier upper bound | `02`–`07` |

## Criteria behind `claim_holds`

* **C2** (k_min smaller under the mean than under the other rule): 1 iff the bootstrap CI of the median paired difference k_other − k_mean lies strictly above 0
  (targets with mean-rank ≥ 2, feasible under both rules).
* **C3** (monotone along the power-mean family): 1 iff ≥ 90% of the targets that are feasible at every p have k_min weakly monotone, in either direction, along p. The direction is reported in `note` / `power_mean_monotonicity.csv`.
* **C4** (feasibility falls with initial rank): 1 iff the bootstrap CI of the Spearman correlation between mean-rank and feasibility lies strictly below 0. If feasibility is constant in the cell (e.g. G1: every target feasible) the claim cannot be tested and `claim_holds=0`, `estimate` empty.
