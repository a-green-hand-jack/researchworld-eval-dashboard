# Rank-stratified full-board sample for Borda and Condorcet (issue #11)

Question: does the OLLB ordinal result (exact MILPs on the 50 best targets only, `results/core_ollb.csv`) hold for targets ranked below 50 on the full
4,496-model board? Run: `python3 code/ordinal_sample.py results/ordinal_sample/shards/sample_K.csv --per-stratum 15 --seed 0 --shard K/4` (K = 0..3, four jobs),
`python3 code/summarize_ordinal_sample.py` (logs `results/logs/ordinal_sample_K.log`; about 5-7 min wall per shard on the shared host).

* **Sample.** 15 targets drawn at random (numpy `default_rng(0)`) from each stratum of the target's rank under the six-task mean: 51-100, 101-300, 301-1000, 1001-max
  (realised ranks 51-4104); **60 targets**, the top of the requested 30-60, chosen because the cost was low (a MILP of at most 1 min). Rules: Borda and Condorcet-winner;
  caps: `emp99` (primary) and `ceil` (100). eps = 1e-3, MILP limit 120 s, HiGHS, finite grid {s, s+eps} (exact on the grid as in `ordinal.py`). The sample is
  stratified by rank, **not** a draw from the population of models: each stratum has the same number of targets whatever its share of the board (50, 200, 700 and 3,500 models), so a pooled share over the 60 targets is not a share of the board and must be read per stratum.
* **Screen.** Each target is first put at the cap-saturated vector (all tasks at their cap); if it is not strictly first there, no raise within the cap can
  make it first (Borda and Condorcet are monotone in the target's scores): `infeasible_screen`, certain, no solver. Otherwise the exact MILP gives L1 and K, and the
  bisection on the saturated uniform lift gives Linf.
* **Counts kept apart** (`summary_status.csv`): feasible (`ok`), infeasible by the screen, infeasible by the MILP (screen passed; possible only at cap edges),
  censored (limit hit; never counted as infeasible). **Nothing was censored or infeasible-by-MILP; all 60 x 2 x 2 targets were decided.**
* **Memory-lean solver.** The dense code builds an (M-1) x K matrix and would not fit for deep targets at M = 4,496; `code/mti/ordinal_lean.py` builds each rival's row on demand and
  adds up the chosen per-task levels to find violated rivals; same MILP, same `_solve`. `code/tests/test_ordinal_lean.py` checks equality with the dense solvers (25 random boards,
  and OLLB targets at ranks 61, 121, 251, both caps, L1 and K).

| cap | rule | stratum 51-100 | 101-300 | 301-1000 | >1000 | all 60 |
|---|---|---|---|---|---|---|
| `emp99` | Borda, feasible / 15 | 15 | 15 | 7 | 0 | 37 of 60 |
| `emp99` | Condorcet, feasible / 15 | 7 | 6 | 0 | 0 | 13 of 60 |
| `ceil` | Borda and Condorcet | 15 | 15 | 15 | 15 | 60 |

Cost (`summary_costs.csv`, `paired_vs_mean.csv`; median over feasible targets, same models and cap as the mean rule, `core_ollb.csv`): at `emp99` the Borda L1 is 0.47 of the mean-rule L1 (bootstrap CI
0.42-0.51; 35 targets feasible under both; Borda cheaper for all 35), Condorcet 0.60 (0.55-0.70; 13 targets); K ratio median 1.0 (Borda) and 1.7 (Condorcet). At `ceil` (60 targets): L1 ratio 0.62 (Borda) and
0.68 (Condorcet), K ratio 3.0 and 2.5 (the rank rules need more tasks raised, each by less). Pairs are selected (targets feasible under both rules), so read the ratio with the
counts `n_both` against `n_sample` and `n_mean_feasible_on_sample` in the file; the mean rule was feasible for 36 of the 60 targets at `emp99`, Borda for 37, Condorcet for 13.

The `all` rows of `summary_status.csv` pool the four equal-size strata (15 targets each, whatever the stratum's share of the board). The pooled share and its exact (Clopper-Pearson)
interval are arithmetic on those 60 targets only: they are not a share or an interval for the board's models (that would need an exchangeability assumption the design does not supply); report the
per-stratum counts. The Borda emp99 L1 ratio interval is 0.42-0.51 (upper endpoint 0.5148 in `paired_vs_mean.csv`).
