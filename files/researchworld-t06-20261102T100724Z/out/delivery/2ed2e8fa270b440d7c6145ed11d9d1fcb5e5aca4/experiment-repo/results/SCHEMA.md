# results/ schema

Every CSV is written by `code/provenance.py::save`; `MANIFEST.json` records for each file the script, seed,
code commit, rows and sha256 of the raw inputs. `*_pilot.csv` are early small runs (MT-Bench-h, NBA 2015).
Scores are natural-log BT scores (theta); ties = half win each; NBA fits include a home-advantage column.

## kstar_full.csv / kstar_units.csv (= kstar_units_nba.csv + kstar_units_arena_mt.csv, joined by merge_units.py)  (one row = one claim x perturbation on one fitted board)
board, design (crowd|expert|model-judge|sports), unit_type (full | nba_season | boot | qboot | subset ...), unit_id,
claim (C1 top-1, C2 adjacent pair order [claim_id = rank r of pair (r, r+1)], C3 top-k set [claim_id = k],
C4 significance of pair (r, r+1) [claim_id = r; only rows where the unperturbed Wald z > 1.96]),
pert (P1 worst-case removal, P2 worst-case relabel/flip, P3 worst-case addition of votes in cells containing the
challenger), k_star (smallest verified k found by greedy influence search + exact refit = UPPER BOUND on the true
minimum; empty when not found), found (False = censored at k_max), k_max (search cap = 0.25 N), k_lin (one-shot
linear/AMIP prediction at the unperturbed fit), N (all comparisons), N_local (comparisons involving the two
participants of the claim; for C1/C3 the pair that attained k_star), n_part, gap (theta_a - theta_b of that pair),
se (Wald s.e. of the gap), z = gap/se, tie_rate.
C1 = min over the 8 nearest challengers; C3 = min over (3 inside, 3 outside)-rank boundary pairs.
Scales: s1 = k_star/N, s2 = k_star/N_local, s3 = z (and B1/B2 tables), s4 = `matched_*.csv`.

## random_curve.csv  (B1)
board, design, N, kind (remove|flip), claim (C1, C2, C4), claim_id, k, n_rep, n_changed = replicates in which the
claim of the unperturbed fit no longer holds after k uniformly random removals / relabels.

## boot_flip.csv  (B2)
board, design, N, claim (C1, C2), claim_id, frac (1.0 = bootstrap with replacement, 0.5 = half subsample w/o
replacement), n_rep, n_changed (= flip count against the full-data claim), gap_se_boot (bootstrap s.e. of the gap;
subsample values rescaled by sqrt(frac/(1-frac))).

## data_summary.csv
board, design, N, n_participants, n_cells, cmp_per_participant, tie_rate, score_range, score_sd, top1.

## matched_arena.csv  (scale s4: size/sparsity-matched Arena subsets)
Same columns as kstar_*, plus n_sub (size curve: votes drawn), score_sd, cmp_per_participant.
unit_type: `mt_dense` (6 Arena models, N matched to MT-Bench-h, dense), `mt_random6` (6 random models),
`nba_like` (30 models, sparse, N and comparisons per participant matched to an NBA season; 72/100 draws had every
claim defined), `sizecurve` (all 64 models, n_sub = 2000..40000 votes, 30 draws each; n_sub = 1000 gave no usable
rows). unit_id = draw index.

## exact_check.csv / approx_check.csv  (validity of the search)
exact_check: source, pert, N, gap, k_greedy, k_exact (exhaustive over all edit multisets, 3-participant boards),
k_lin, exact_capped (True = exhaustive search stopped at k = 14; excluded from the 262-instance agreement count).
approx_check: board, rank, pert, m_edits, frac_of_kstar_P1 (edit budget as a fraction of k*), gap0, pred_change
(influence prediction of the gap change), actual_change (exact refit).

## sensitivity.csv  (E5 modelling choices)
kstar columns plus `variant`: tie_half (reference) | tie_dropped (Arena, MT-Bench), no_home (NBA), with_playoffs,
pooled_5/10/20 (NBA seasons pooled). unit_id = season or `full`.

## sens_aba.csv
kstar columns plus `variant` (league_all / league_nba etc.): NBA seasons by league era (BAA/NBA/ABA).

## elo_order.csv  (exploratory: BT vs online Elo, arrival order)
board, K (Elo step), n_perm random arrival orders, tau_elo_vs_bt (Kendall tau of Elo ranking vs BT, mean/sd),
tau_perm_vs_ref (Elo under permuted vs reference order), p_top1_same_as_ref / _as_bt (share of orders with same top-1).

## sanity_fit.csv / alignment.csv  (E0 checks)
sanity_fit: per NBA season, Kendall tau of BT vs FiveThirtyEight Elo and vs win rate, top-1 under each, same_top1.
alignment: item, n  (MT-Bench key counts: human rows, unique keys, keys shared with GPT-4, ...).

## summary_claims.csv  (E4: distribution of k* over replicate units)
board, design, unit_type, claim, pert, n_rows, n_units, frac_found (share not censored), k_median/k_q025/k_q975,
kN_*(k*/N), kNloc_median (k*/N_local), z_median, frac_z_lt_196, N_median, n_part. Censored rows enter at k_max.

## paired_mt.csv  (E4: human vs GPT-4 on the same resampled questions)
a (human board), b (GPT-4 board): (mtbench_human, mtbench_gpt4) all keys; (mtmatched_h, mtmatched_g) the aligned
keys, all human judgments; (mtmatched_h1, mtmatched_g) aligned keys, one random human judgment per key.
Per claim x claim_id x pert, over the n_units shared question-cluster bootstrap replicates: logratio_k_* =
log(k*_b / k*_a) (positive = the GPT-4 board needs more edits), median and 2.5 / 97.5 percentiles;
logratio_kN_* the same for k*/N; dz_* = z_b - z_a. Needs >= 20 shared replicates.

## scaling_fit.csv  (E4: log k* ~ log z + log N_local)
OLS on rows with found, k* >= 1, z > 0.02, per claim x pert. model: M0 (const, log_z, log_Nlocal), M1 (+ design
dummies, reference = crowd). `scheme` = bootstrap used for ci_lo / ci_hi (B = 2000, percentile): `unit` resamples
replicate units (within-dataset sampling only; replicates of one dataset are dependent, so conditional on the
datasets), `dataset` resamples independent datasets (NBA seasons, Arena, MT-human, MT-GPT-4 as one cluster each;
M0 only, since crowd / expert / judge dummies are single-dataset contrasts). n_boot_ok = bootstrap draws kept,
n_clusters, resid_sd and r2 on the log scale.

## se_check.csv
Wald s.e. of the C2 gap (kstar_full) against the bootstrap s.e. (boot_flip, frac = 1): board, claim_id, se, z, gap,
tie_rate, gap_se_boot, n_rep, n_changed, se_ratio_wald_over_boot, z_boot.

## kstar_judges.csv  (matched crowd vs model judge, identical Arena battles)
kstar columns for boards `arena49k_h` (human votes) and `arena49k_<judge>` (Meta-Llama-3-70B-Instruct, Athene-70B,
Qwen2-72B-Instruct), only the 49,938 single-turn battles shared with the judge dataset; unit_type `full` (unit_id -1)
and `boot` (40 shared battle-bootstrap resamples); claims C1, C2, C4; perts P1, P2. `paired_mt.csv` rows with
a = arena49k_h hold the paired contrasts.

## summary_claims.csv, added columns
z_q025 / z_q975 (spread of the unperturbed z over units), n_resolved (rows with |z| >= 1.96), k_median_resolved /
k_median_unresolved (median k* of rows whose claim was / was not already resolved by the data before any edit).
