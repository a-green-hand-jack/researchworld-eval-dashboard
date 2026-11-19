# Figure and table spec (working, figtab-repo)

Claim numbers refer to `PLAN.md` section 5 (story-repo). Everything is drawn from `results/` of experiment-repo; nothing typed by hand.
Global encoding: one colour per evaluation design, identical in every figure (Okabe-Ito, colour-blind safe, distinct also in greyscale by marker):
A crowd votes (blue, circle) | M-h expert (vermillion, square) | M-g model judge (orange, triangle) | N sports (bluish green, diamond); M-h and M-g are a matched pair and differ by marker fill as well as hue.
Size scales are always on log axes; same limits across panels of one figure; intervals are 95% unless stated, and the caption names the replication unit (battle bootstrap for A, question cluster bootstrap for M-*, seasons for N).
A k* is an upper bound (verified perturbation found), so a search that found nothing within the budget is drawn as a right-censored arrow, never as a point.

| id | claim it must support | encoding | needs from results/ |
|----|-----------------------|----------|---------------------|
| T1 | data and design summary (context for all) | table: design, N comparisons, participants, comparisons/participant (median, min), tie rate, unit of replication, source commit, sha256 | `data_summary` |
| F1 | C1 fragility per dataset (claim 1) | dot plot, rows = ranking claim (C1, C2 weakest adjacent pair, C3 k=3/5/10, C4), columns = dataset; x = k*/N (log) with interval; NBA seasons as median+IQR with the seasons as light dots; censored = arrow; second x-axis in absolute k | `kstar`: one row per (dataset, unit [season/replicate], claim, perturbation P1/P2/P3), k_star, found flag, k_max_searched, N, N_local, n_participants, interval lo/hi and how made |
| F2 | worst-case vs random vs bootstrap (claim 2) | per dataset small multiple, claim C1 and weakest C2 pair: P(claim changes) vs removal size k/N (log); random-removal curve with band; vertical line at worst-case k*; marker where bootstrap resampling moves the claim with prob 0.5 (s3) | `random_curve`: (dataset, unit, claim, perturbation, k grid, n_rep, n_changed); `boot_flip`: P(claim differs across bootstrap replicates) per claim |
| F3 | designs differ? on s1-s4 (claim 3) | 4 panels s1 k*/N, s2 k*_local fraction, s3 k*/k_random50 and z-gap, s4 matched-size Arena subsets; designs by colour | s1-s3 columns of `kstar`; `matched`: Arena subsets matched to MT-Bench and to an NBA season (target, rep, k*, N, participants, comparisons/participant) |
| F4 | matched contrast M-h vs M-g (claim 3) | paired plot: same claim/same model pair, two judges, interval on each, difference with CI | `kstar` rows for M-h and M-g with identical claim ids |
| F5 | what predicts fragility (claim 4) | scatter log k* vs log z-gap (and k*/N), colour by design, OLS/rank-correlation line with CI band, slope + CI in the panel; second panel predictors (comparisons/pair, tie rate) | `kstar` joined to `claim_stats`: z-gap, score gap, comparisons for the pair, tie rate, n_participants |
| F6 | where the method is loose (claim 4) | (a) influence-predicted vs refit-verified change (log-log, y=x line); (b) ratio k*_greedy / k*_exact on small instances | `approx_check`: (dataset, claim, k, predicted, refit); `exact_check`: (instance, claim, k_greedy, k_exact or bound) |
| T2 | headline numbers (claims 1-3) | rows dataset x claim, columns P1, P2, P3, random-removal k50, bootstrap size: k* [lo, hi] and k*/N | tidy `kstar` summary produced by the generator, not by hand |
| T3 | conditions of validity (claim 5) | sensitivity table: change in k*/N for ties handling, home/position covariate, Elo vs BT ranker, order, greedy vs one-shot | `sensitivity` (E5); also Arena time-split and NBA early/late eras if run |

Two-column paper: figures are drawn at the venue's text width (full) or column width (half); fonts at least 7 pt at final size.
Not claimed by any figure: BT misspecification as a mechanism, anything about manipulators' real behaviour (text-only in the paper).
