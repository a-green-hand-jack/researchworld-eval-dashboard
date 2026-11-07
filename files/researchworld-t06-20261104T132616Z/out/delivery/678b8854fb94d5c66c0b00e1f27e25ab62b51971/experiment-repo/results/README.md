# Results: definitions and file schemas

Everything here is produced by the code in `../code` (commands and run times: `../code/REPRODUCE.md`). Every `*.meta.json` records the
code revision (`code_rev`; `+dirty` would mean uncommitted changes under `code/`), package versions, the data files with
sha256 and source, the script and its arguments. Rows with `synthetic=True` (or `kind=syn`) are SYNTHETIC data drawn from a
fitted model, never real comparisons.

## 1. Definitions (as implemented)

**Data model.** A comparison is an ordered pair of participants `(i, j)` and an outcome `i wins / tie / j wins`.
Comparisons are aggregated into cells (participant pair, home flag, outcome) with integer counts `n_po`; every perturbation is
a change of these counts. Arena 55k: a tie is `winner_tie = 1` (both "tie" and "both bad"). MT-Bench: each row of the human
file (one expert judgment on a (question, turn, model pair)) is one comparison, so a key judged by several experts counts several
times; the GPT-4 file's `tie (inconsistent)` (its verdict flipped with the answer order) is a tie. NBA (538 `nbaallelo.csv`):
one row per game (`_iscopy == 0`), regular season only (playoffs only in an ablation), participants are franchises (`fran_id`),
no ties.

**Estimator.** Bradley-Terry: `P(i beats j) = sigmoid(theta_i - theta_j [+ beta h])`. A tie is half a win for each side (soft
label `s = (1, 1/2, 0)` for `i wins / tie / j wins`). Loss = `sum_cells n_po * CE(sigma(d_p), s_o) + (lambda/2) ||theta||^2`
with `lambda = 1` (also `lambda = 0.01, 100` in the ablation), no intercept, no sum-to-zero constraint (the ridge centres the
scores). The home advantage `beta` (penalty 1) is only in the `home_param` ablation. Fitted by Newton with backtracking
(gradient tolerance `1e-9 * max(1, sqrt(N))`), validated against scikit-learn's L-BFGS logistic regression on a row-level
design (`validation_fitter.csv`, max |theta difference| below 1e-4 on all four base datasets). Reported scores are on the Elo scale
`theta * 400 / ln 10`.

**Claim sets and claims.** Claims concern the participants ordered by the base fit `pi(1) .. pi(K)`. MT-Bench and each NBA season: all
participants (window W = K). Arena 55k and NBA-all (K = 64 / 53): the *window* is the top W = 20 ranks of the base fit (not the 20 most compared models);
C2 and C4 are about the window, but the challengers of C1 and C3 are **all** participants, so a runner-up outside the window cannot be missed (an earlier
version used the 20 most-compared models and missed the Arena runner-up `gpt-4-0125-preview`; reported by `internal-review-repo`, `experiment-repo#6`).
The 20-most-compared set is kept as the secondary claim set `arena55k_top20count` / `nba_all_top20count` (all challengers among those 20 only).
A claim is *true* in a perturbed data set if it holds for the perturbed fit and *flipped* otherwise.
- **C1 (top-1)**: `pi(1)` is the argmax of theta over all participants.
- **C2_r (adjacent pair), r = 1..W-1**: `theta_pi(r) > theta_pi(r+1)`. In `claim_id` the index is zero-based (`c2_0` is rank 1 vs 2) and `rank` is r.
- **C3_k (top-k set), k in {3, 5, 10}, k <= W-2**: the k best of all participants are the base top-k set (any order). Flipped iff some
  member of the base top-k falls to or below some non-member.
- **C4 (Kendall tau)**: `(concordant - discordant) / (W(W-1)/2)` between base and perturbed theta over the W window participants, reported as
  mean and 5th percentile over seeds (random perturbations only).
Claims are defined relative to the base order and are not independent (adjacent pairs share participants).

**Perturbations.** *Random removal*: `round(f N)` comparisons removed uniformly without replacement (multivariate hypergeometric over
cells). *Random label flips*: each comparison is relabelled with probability `f` to one of the other outcomes uniformly (two others when
ties exist). *Bootstrap*: multinomial resample of N comparisons. 200 seeds per fraction `f in {0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5}`; bootstrap B = 1000. Seeds are
`default_rng([base_seed, f_index, s])`. *Adversarial removal* (primary), *adversarial addition* (add comparisons of existing
participant pairs, home flags and outcomes, up to 50 N) and *adversarial relabelling* (change the outcome of existing
comparisons): the smallest number of comparisons found whose change makes a given pair satisfy `theta_a - theta_b <= 0`.

**Adversarial budget (`budget`).** For one pair, the number of comparisons of the perturbation found by the search below.
For a claim, the minimum over its candidate pairs: C2: the pair itself; C1: `(pi(1), b)` for every other `b`; C3_k: every
`(i, j)` with `i` in the base top-k and `j` outside. Search: *greedy with exact refits*: linearise the fitted model around the
current fit (influence of a unit change of cell `(p, o)` on the gap: `(s_o - sigma_p) r_p` with `r = V H^-1 u`,
`H` the Hessian, `u` the contrast of `a` and `b`), take the cells with the largest gain, in chunks of `ceil(0.3 x remaining estimate)` comparisons
(single steps when the estimate is at most 6), refit exactly after every chunk, bisect on the chunk that flips; then *polish*
(swap/drop local search). **The budget is a verified upper bound on the minimum**: the perturbation was refitted exactly and
the claim does flip; it is not proven minimal. Validation of minimality: `method_validity.csv` (other heuristics, one-shot
linearised ranking, the linear estimate itself) and `method_validity_exhaustive.csv` (exact minimum by enumeration on small
MT-Bench subsamples). `verified = True` when a flipping perturbation was found; otherwise the row is *censored*
(`search_status = not_found_exhausted_all_comparisons`, `budget = NaN`). `exact_tie = True` when the base gap is below 1e-9 (the
claim is not a strict order to begin with; excluded from the regressions).

**Size scales.** With `k` the budget, `N` all comparisons of the data set, `n_a, n_b` comparisons involving participants a, b
and `n_ab` the comparisons between them:
- `budget_frac_N = k / N`; `budget_frac_pair = k / (n_a + n_b - n_ab)` (fraction of the comparisons that involve a or b);
  `k_per_sqrtN = k / sqrt(N)`.
- **`budget_noise_units` (noise-equivalent unit, "leverage") = gap / SD(shift of the gap under uniformly random removal of the same k comparisons)**
  (SD over 200 random removals). Larger = the adversary gets with k removals a shift that random removal of k produces only as an
  L-sigma event. `rand_flip_prob_at_k` is the fraction of those 200 random removals that flip the claim pair.
  **Near-identity:** under random removal of k of N comparisons the gap's SD is about `se_gap * sqrt(k / (N - k))`, hence
  `budget_noise_units ~ z_gap * sqrt((N - k) / k)` (column `leverage_identity`; measured ratio to `budget_noise_units`: median 0.98-1.04 on every dataset,
  correlation of logs 0.995 over all claims). The leverage therefore carries no information beyond `z_gap` and `k / N`; it is a re-expression
  of the budget fraction in units of the claim's own statistical margin, and it is near-constant (about 30-40) across ranks of one dataset because
  the budget scales roughly like `z_gap * sqrt(n_pair)` (E4).
  The plan's "one SE" unit is degenerate: random removal of a fraction r moves the gap by SD `SE sqrt(r / (1 - r))`, so 1 SE corresponds to
  r = 1/2 on every data set.
- **`z_gap` = gap / `se_gap`**, `se_gap` the SD of `theta_a - theta_b` over 1000 bootstrap resamples; `p_boot_pair_holds` the
  share of resamples in which `a` stays above `b`.
- Pair-level descriptors: `n_pair_comparisons` = `n_ab`, `n_pair_involving` = `n_a + n_b - n_ab`; `n_min_participant` = min(`n_a`, `n_b`) and `sparse_pair = n_min_participant < 200` (descriptive flag: a participant with few comparisons is not reliably rankable; many of the smallest budgets involve such participants).

**Regressions (E4).** Sample: strictly ordered adjacent-pair claims (C2, base gap > 1e-9) with a verified budget; datasets: Arena 55k, MT-Bench
human, MT-Bench GPT-4 and the 69 NBA regular-season fits (the NBA full-history fit is an ablation and is not in the regressions).
OLS of `log k` on: `log z_gap` (M0); `+ log n_pair_involving` (M1); the influence signal-to-noise `log infl_snr` (M2); `log z_gap + log infl_snr` (M3, M4 adds `log n_pair_involving`);
`log gap + log n_pair_involving` (M5). `infl_snr = gap / infl_sd`, where `infl_sd` is the SD over all N comparisons of the linearised
change of the gap caused by removing that comparison (`s3_influence.csv`; `infl_rho` = mean of the k largest influences / `infl_sd`).
Each model is fitted per dataset and pooled with dataset-specific intercepts (reference: NBA seasons) and weights 1/(claims of the dataset);
there is no inference about "design" across datasets (one crowd, one expert, one LLM-judge data set, 69 sports seasons).
Uncertainty: bootstrap B = 2000 resampling claims within a dataset and, for NBA, whole seasons (cluster bootstrap); claims within a data
set are not independent. MT-Bench has 5 adjacent-pair claims per judge, too few for regressions (its budgets are reported with intervals instead).

## 2. Files

Stage 0 (`code/s0_base.py`): `summary_datasets.csv` (`dataset_summary.csv` is the raw version), `base_scores.csv` (`base_<unit>.csv` raw), `validation_fitter.csv`.
Stage 1 (`code/s1_run.py`, `code/s1_exhaustive.py`, collected by `code/s2_collect.py`): `parts/` (one file per unit), `random_all.csv`, `budgets_remove.csv` (raw collected columns), `s1_exhaustive.csv`.
Stage 2 (`code/s2_controls.py`, `code/s2_matched.py`, `code/s3_models.py`): `s2_controls_syn_sub_arena6.csv`, `s2_matched_{budgets,scores,agreement}.csv`, `s3_influence.csv` (from `code/s3_influence.py`), `s3_models_{coef,bins}.csv`.
Stage 3 (`code/s3_extra.py`): `s3_rigging.csv`, `s3_ablations.csv`, `s3_uncert.csv`.
Tidy tables (from `code/s4_export.py`, pure post-processing of the above): the files named in the table below.

| file | claim | one row per | key columns |
| --- | --- | --- | --- |
| `summary_datasets.csv` | E1 | data set | design, K, K_eligible, N, n_tie, tie_frac, pair-count min/median/max, frac_pairs_unobserved, claim_set |
| `base_scores.csv` | E1 | eligible participant | score (Elo), ci_lo, ci_hi, se, rank, rank_lo, rank_hi |
| `random_survival.csv` | E2 | data set x perturbation x f x claim | p_survive over n_seeds, Wilson ci_lo/ci_hi |
| `random_tau.csv` | E2 | data set x perturbation x f | tau_mean, tau_p05 |
| `adv_budgets.csv` | E3, E4 | data set (or NBA season) x claim | budget, budget_frac_N, budget_frac_pair, budget_noise_units, z_gap, n_pair_comparisons, verified, search_status, budget_lo/hi |
| `regression_coef.csv` | E4 | model x term | coef, ci_lo, ci_hi, r2, n_claims |
| `matched_labeller.csv`, `matched_pairs.csv` | E5 | variant x claim / pair | the same pair under two labellers: gap, budget, z |
| `method_validity.csv`, `method_validity_exhaustive.csv` | E6 | claim x method / instance | budget, ratio_to_best_verified, exact |
| `ablations.csv`, `ablations_summary.csv` | E7 | variant x data set x claim | budget, frac_N; median frac_N with claim-level bootstrap interval |
| `additions.csv` | E8 | claim | budget_add, budget_relabel, budget_remove and ratios |
| `controls.csv`, `control_comparison.csv` | E4 | control run x claim / group | `synthetic` flag, budget, z, N-matched subsample fits |

## 3. Additional analyses (second round: cluster SE, constrained adversary, published-output claims, estimators, intervals, first-order budget, windows)

All are written by `code/s5_*.py` (command map in `code/REPRODUCE.md`). Budgets are verified upper bounds throughout (an exact refit of the perturbed counts flips the claim); `NaN` = no flip found.

| file | request | one row per | key columns |
| --- | --- | --- | --- |
| `s5_cluster_se.csv` | #7 | unit x claim of `budgets_remove.csv` | `se_gap_iid`, `se_gap_cluster` (SD of theta_a - theta_b over B = 1000 cluster-bootstrap refits), `z_iid`, `z_cluster` = gap / se_gap_cluster, `p_cluster_pair_holds`, `n_clusters`, `cluster_type` (MT-Bench: question, 80 clusters; Arena: identical prompt text, 51,734 clusters, the file has no user or conversation id and 3,118 prompts occur more than once; NBA season: 7-day week of the season; pooled NBA: season) |
| `s5_z_shares.csv` | #7 | dataset | shares of adjacent-pair (C2) claims with z < 1 and z < 2 under both bootstraps, `median_se_ratio` = cluster / iid SE |
| `s3_models_coef.csv` (models `M0c`, `M1c`) | #7 | scope x model x term | the budget-vs-z regressions refitted with `log z_cluster` (pooled with dataset intercepts, and per dataset) |
| `s5_constrained.csv` | #8a | unit x claim | `budget_con_add_a_down`, `..._add_b_up`, `..._relabel_a_down`, `..._relabel_b_up`: constrained adversary (all added / relabelled comparisons involve the target: `a` pushed down or `b` pushed up; the opponent of each is allocated in proportion to the target's observed pair frequencies, no free choice of opponent, no third-party votes); `budget_con_add`, `budget_con_relabel` = min over the two sides. Compare with `additions.csv` (unconstrained) and `budgets_remove.csv` (removal) |
| `s5_noise.csv` | #8b | unit x claim | `k_noise_05`, `k_noise_50`: smallest number of uniformly random removals (Monte-Carlo, 200 draws per k on a 36-point geometric grid, log-linear interpolation) at which the claim (C1, C2_r, C3_k as defined, not only the argmin pair) is flipped with probability >= 5% / 50%; `NaN` = frequency stays below the level up to 98% of N; `flip_freq_at_1pct_N`, `max_flip_freq_grid` |
| `s5_published.csv`, `s5_published_summary.csv` | #9a | unit x claim | claims on the published output. `c2ci_r`: the 95% percentile-bootstrap interval (B = 200, iid) of theta_a - theta_b of adjacent pair r excludes 0 (`lo95`, `hi95`, `se_boot`, `base_holds`); `c1p`: the top participant keeps the rank interval [1, 1] among all participants (`p_rank1` >= 0.975, `rank_hi` = 97.5th percentile of its bootstrap rank). `budget` = smallest removal after which the claim is false when the perturbed counts are RE-BOOTSTRAPPED (0 if already false at base), found by a bisection over the target `gap <= t * se_boot` (`t_used`) with every candidate verified; `budget_point` = the point-gap flip budget of the same pair. Units: arena55k, mt_human, mt_gpt4, nba_all and the seasons 1950, 1960, ..., 2010 (every tenth season from 1950, fixed before looking at results) |
| `s5_budget_intervals.csv` | #10b | dataset x statistic | the base-fit C1 budget and the median C2 budget (`statistic` = `c1`, `median_c2`; `base_budget`, `base_frac_N`) with the 2.5-97.5 percentile (`lo95`, `hi95`), min and max of the same statistic over the dataset-bootstrap resamples of `s3_uncert.csv` (`resamples` of them; the median C2 is taken per resample over the flipped C2 claims with a positive gap). It is conditional on the claim set of the base fit; in each resample the claims (top-1 and adjacent pairs of the window) are defined on that resample's own ranking, so the interval includes change of identity of the claim; resamples where the claim is not flipped are excluded |
| `s5_estimator.csv`, `s5_estimator_rank.csv` | #9b | dataset x variant x claim / dataset x variant | C1 and C2_r budgets under `base` (L2 lambda = 1; a tie is a half win), `lam_1e-6` (practically unregularised), `drop_ties`, `tie_wl` (a tie = one win + one loss); each variant has its own base ranking and top-20 window; `_rank`: top-1 identity, window overlap and Kendall tau of the variant scores against the base scores on the base window. FastChat's `compute_bt` labels a draw 0.5 (soft target) exactly as the base fit does; its plain BT fit has no penalty, its style-control fit L2 0.5 |
| `s5_restarts.csv`, `s5_restarts_summary.csv` | #10a | unit x C1 / C2 claim | 50 randomised restarts of the greedy+polish removal search (noisy gain order, random chunk fraction) on the budget-defining pair: `budget_det`, `restart_min/median/max`, `share_le_det`, `lin_est` (first-order estimate). Empirical check of the search, not a certificate |
| `s3_uncert.csv` | #10b | unit x claim | dataset-level resampling intervals of the budgets (`budget_lo`, `budget_hi`) |
| `s5_control_draws.csv`, `s5_control_summary.csv` | #10c | draw x claim / statistic | Arena six-model battles (1,367, bootstrap resamples) vs MT-Bench human (1,367 of 3,355, subsamples): 40 draws each; `median_share` and interval over draws, `min_detectable_ratio` from label permutations (draw-level and claim-level, five independent adjacent-pair claims) |
| `s5_khat.csv`, `s5_oos_summary.csv`, `s5_collinearity.csv` | #11 | claim / dataset | `k_hat` = ceil(first-order estimate), `khat_over_k`; out-of-sample prediction of log budget from a log-z line fitted on NBA seasons only (no dataset intercept): bias, RMSE, bootstrap interval, same for log k_hat; correlations and VIFs of log z, log SNR, log n_pair. **Collinearity caveat:** corr(log z, log SNR) = 1.000 on Arena (VIF about 10^4), 0.988 on NBA seasons, 0.972 pooled, so the coefficients of `log_snr` and `log_z` in M2-M4 are not separately identified and "SNR adds nothing beyond z" cannot be tested; cite M0/M1 (and M0c/M1c) only |
| `s5_window_sweep.csv`, `s5_window_budgets.csv`, `s5_window_support.csv` | #6 | window rule x size | C1, median C2, C3_k budgets for windows top-w by score (w = 10, 20, 30, 40, all) and top-n by number of comparisons; support: share of comparisons inside / touching the window, least-compared member, adjacent pairs with >= 100 direct comparisons |
| `s5_nba_eras.csv`, `s5_nba_eras_pairs.csv` | #6 | franchise / franchise pair | first and last season, seasons, games, base rank; `common_seasons`, `direct_games` per franchise pair (the pooled fit gives each franchise one constant strength over 1947-2015) |
