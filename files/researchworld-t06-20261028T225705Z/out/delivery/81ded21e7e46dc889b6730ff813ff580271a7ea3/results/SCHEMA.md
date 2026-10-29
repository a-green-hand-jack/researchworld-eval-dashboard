# Result files (tidy CSV; every file is written by the script named in REPRODUCE.md)
Common columns: `dataset`, `eval_design` (crowd | expert | model_judge | sports), `N` comparisons, `p` participants, `seed`.
Budgets are numbers of comparisons altered, `budget_k`, and `budget_frac = budget_k/N`; **every adversarial budget is an upper bound on the true minimum** (an attack found and verified by exact refit); `NaN` = no attack found within 50% of N.

| file | content |
|---|---|
| `decisions_<ds>.csv` | `replicate` (-1 = original data, >=0 = bootstrap resample of comparisons), `decision` (top1, topk3/5/10 = set of top-k changes, tau0.95/0.9 = Kendall tau vs original ranking falls below), `method` (influence_exact = influence-ranked greedy + exact refit; baseline_direct = only head-to-head comparisons of the target pair may be altered; baseline_involving = only comparisons involving either target; influence_exact_greedy = tau attack), `perturbation_type` (drop, flip, add_a_wins, add_b_loses = injected votes for the promoted target / against the leader), `budget_k`, `budget_frac`, `pair` (cheapest target pair "upper>lower" for drop/flip, "promoted>leader" for add) |
| `adjacent_pairs_<ds>.csv` | every adjacent pair of the original ranking: `phi` (BT score gap), `se_phi`, `z`, `n_ab` head-to-head comparisons, `k_drop,k_flip` (influence_exact), `k1_*` (first-order estimate before refit), `k_direct_*`, `k_involving_*` baselines |
| `benign_<ds>.csv` | random_drop / random_flip (m comparisons) and bootstrap (size N): `metric` p_top1, p_topk3/5/10, p_tau<0.95, p_tau<0.9 (`value`, Wilson 95% `ci_lo/ci_hi`), tau_mean (percentile interval), `n_draws` |
| `benign_pairs_<ds>.csv` | per adjacent pair (original ranking): `phi0`, `sd_dphi` (SD of the gap under benign perturbation of size `budget_k`), `p_flip` |
| `scores_<ds>.csv` | per participant: BT `score` (centred, log-odds), bootstrap 95% `ci_lo/ci_hi`, `rank`, `rank_lo/rank_hi`, `n_comparisons` |
| `nba_seasons.csv` | one row per NBA regular season: `z_top`, `top1_*`, `adjmin_*` budgets |
| `commonN.csv` | common-size control: `control` N (N0=2000 comparisons, all participants) or N+p (N0=2000, 6 participants), `replicate`, budgets |
Data versions and checksums: `code/00_fetch_data.sh`. BT model: ties = half win, ridge 1e-3, NBA with one shared home-advantage parameter.
| `pubrank.csv`, `pubrank_summary.csv` | Arena-style published rank (1 + #models whose Wald-95% CI lower bound exceeds this model's upper bound) vs point rank per participant; effect of the cheapest verified top-1 attack on published ranks (`code/10_pubrank.py`) |
| `sensitivity.csv`, `synthetic.csv` | C5 modelling-choice variants; SYNTHETIC BT calibration worlds (never headline results) |
| `summary_*.csv` | post-processing by `code/06_summaries.py`: `summary_decisions` (original budget, bootstrap median/95% over resamples, k relative to participants' comparisons, benign random-perturbation flip probability bound), `summary_b50` (subsample scale b_q, q=.1/.25/.5, with `flag` below_grid/above_grid censoring), `summary_fragility_vs_gap`, `summary_groups` |
