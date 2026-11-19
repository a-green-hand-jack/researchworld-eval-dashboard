# Reproducing the results

Everything is analysis of public score tables on CPU: no model is trained or evaluated, no GPU is used. Run all commands from the `code/` directory of the delivery
(the same layout as the root of the analysis repository). Raw run files are written to `results/raw/`; the tables of `results/` are rebuilt from them.

## Environment

Python 3.11.2; numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, pyarrow 26.0.0, scikit-learn 1.9.1, highspy 1.16.0 (HiGHS, used through `scipy.optimize.milp`).
`pip install numpy scipy pandas pyarrow scikit-learn highspy` is enough; no other package is imported. Solvers run single-threaded (the only solver settings are a per-solve time limit, 30 s in the E1 runs, and a MIP relative gap of 1e-9), so results do not depend on the number of cores. All random draws use `numpy.random.default_rng` with the seeds listed below; every
shard of a run uses the same seeds, so any sharding of a run gives the same rows.

## Data (frozen versions, no later download is used)

| source | version | where | integrity |
|---|---|---|---|
| HELM MMLU (79 models x 57 subjects, accuracy) | HELM release v1.13.0 of 2025-01-10 (GCS bucket `crfm-helm-public`, `mmlu/benchmark_output/releases/v1.13.0`) | `scripts/fetch_helm.py` -> `scripts/prep_helm.py` | `data_meta/helm_v1.13.0_manifest.json`: path, size, sha256 and GCS md5/generation of every file read |
| Open LLM Leaderboard `contents` (6 benchmark scores per model, 2025-03-20 snapshot) | dataset repo `open-llm-leaderboard/contents`, commit 9c09a7cae43334062a82cb164f2ef255013dafa2 | `scripts/prep_ollb_boards.py` | sha256 of the derived tables printed in `boards.csv` (`sha` column) |
| Open LLM Leaderboard `results` (raw per-sub-task scores, 2025-03-15 snapshot) | dataset repo `open-llm-leaderboard/results`, commit aa81ecc38fdc5708254b833923368970efdf5ef5 | `scripts/prep_ollb_results.py`, `scripts/prep_ollb_boards.py` | same |

`data_proc/` holds the derived tables (11 MB; the raw downloads are not shipped because of the size limit and can be regenerated with the fetch/prep scripts). Models of the `results`
snapshot are matched to the `contents` rows on (full name, model sha) and accepted only if the results file reproduces the `contents` score (IFEval and MMLU-Pro agree to 1e-3).
The `results` snapshot has no MMLU-Pro subject scores, so the OLLB sub-task board has m = 39 tasks (BBH 24, GPQA 3, MuSR 3, MATH 7, IFEval 1, MMLU-Pro as 1 task). Its benchmark
level ("m6raw", the six benchmark means of the sub-task scores) approximates but is not identical to the normalised `contents` score ("m6").
Licences of the sources are those of the HELM release and of the two Hugging Face dataset repositories; the derived tables are redistributed as processed numbers only.

## Seeds

HELM subset draws (E2): `default_rng([20260101, m, d])`; E6 noise: `default_rng([20260301, target, rule])` (E6b: the same stream for the margin grid, `[20260302, target, rule]` for the plan-sd variant); E5 random developer: `default_rng([20260401, target, rule])`;
calibration bootstrap: 20260102; cluster bootstraps in `analysis/stats.py` (a clustering scheme with fewer than 5 clusters, such as an incumbent that is one model for all targets but one, is dropped from the union of schemes when another has enough): a fixed seed per call site (set in the calling script), 2000 resamples (`NBOOT` overrides).
Exact solvers are deterministic.

## Commands (order of dependence)

```
# data
python3 scripts/fetch_helm.py data_raw/helm data_meta/helm_v1.13.0_manifest.json ; python3 scripts/prep_helm.py data_raw/helm data_proc
python3 scripts/prep_ollb_results.py data_raw/ollb_results data_proc ; python3 scripts/prep_ollb_boards.py data_raw/ollb_contents.parquet data_proc
# solver verification (brute force on small instances; minutes)
python3 scripts/run_checks.py results/solver_check_tests.csv 200
# experiments (each writes one raw CSV; shards are independent and may run in parallel)
python3 scripts/run_e1_helm.py results/e1_helm_points_s$s.csv $s 2 points            # s = 0, 1   E1/E3 HELM (79 targets, 9 rules, B grid)
python3 scripts/run_e1_ollb.py m6 results/e1_ollb_m6_points.csv 0 1 points            # E1/E3 OLLB benchmark level, top-30
python3 scripts/run_e1_ollb.py m39 results/e1_ollb_m39_points.csv 0 1 points          # E1/E3 OLLB sub-task level, top-30
python3 scripts/run_frontier.py helm results/frontier_helm.csv 30 ; python3 scripts/run_frontier.py m6 results/frontier_ollb_m6.csv 30
python3 scripts/run_e2_helm.py results/e2_helm_s$s.csv $s 2                           # s = 0, 1  m = 5, 9, 15 (60 draws), (25, 41, 57 see next line)
python3 scripts/run_e2_helm.py results/e2_helmbig_s$s.csv $s 4 30 10 25,41,57         # s = 0..3  m = 25, 41 (30 draws), 57 (1 draw)
python3 scripts/run_e2_ollb.py results/e2_ollb_s$s.csv $s 3 30                        # s = 0..2  bundled (m6raw) vs free (m39) at the same models
python3 scripts/run_e2_ollb.py results/e2_full_helm.csv 0 1 79 helm                   # sigma-unit price on the full HELM board (R1 budgets)
python3 scripts/run_r1.py helm results/r1_helm_s$s.csv $s 3 30 ; python3 scripts/run_r1.py m6raw results/r1_m6raw.csv ; python3 scripts/run_r1.py m39 results/r1_m39_s$s.csv $s 3
CGRID=0.5,0.75,1.25,3,4,6,8 python3 scripts/run_r1.py helm results/r1x_helm_s$s.csv $s 3 30   # crossing-budget grid (also m6raw -> r1x_m6raw.csv, m39 -> r1x_m39_s$s.csv)
python3 scripts/run_units.py helm results/units_helm.csv 0 1 30 ; python3 scripts/run_units.py m6raw results/units_m6raw.csv 0 1 30 ; python3 scripts/run_units.py m39 results/units_m39_s$s.csv $s 2 30
python3 scripts/run_calibration.py results_tables
python3 scripts/run_e5.py results/e5_$b.csv $b 0 1 30 60                              # b = helm, m39
python3 scripts/run_e6.py results/e6_helm.csv helm 0 1 30 60 400 ; python3 scripts/run_e6.py results/e6_m39_s$s.csv m39 $s 2 30 60 400
python3 scripts/run_e6b.py results/e6b_helm.csv helm 0 1 30 60 400 ; python3 scripts/run_e6b.py results/e6b_m39_s$s.csv m39 $s 2 30 60 400   # E6b: wider margin grid, margin from the boosted plan's sd
python3 scripts/run_e7.py results/e7_m6.csv 0 1 30
# tables and statistics
python3 scripts/make_results.py results_tables                    # price, m_effect, solver_check, frontier, boards, calibration (+ sidecars)
python3 analysis/run_analysis.py results_tables ; python3 analysis/r4.py results results_tables ; python3 analysis/units.py results results_tables
python3 analysis/predictors.py results_tables ; python3 analysis/predictors_norm.py results_tables ; python3 analysis/e6b.py results results_tables ; python3 analysis/e5.py results results_tables ; python3 analysis/e6.py results results_tables ; python3 analysis/e7.py results results_tables
python3 analysis/spillover.py results_tables results_tables ; python3 analysis/verdicts.py results_tables results
python3 analysis/magnitude.py results_tables ; python3 analysis/predictors_within.py results_tables ; python3 analysis/flip.py results_tables results ; python3 analysis/hl.py results_tables ; python3 analysis/bx.py results_tables results        # exploratory H-L (deficit profile) and the crossing budget B_x
python3 scripts/make_results.py results_tables analysis_meta      # sidecars of the tables written by analysis/
python3 analysis/headline.py results_tables results/headline.json
```
(`scripts/sync_delivery.sh` copies code, raw runs and tables into the delivery layout.) The exact commands used for each run are the ones above; `python3 scripts/<script>.py` without
arguments prints the usage line.

## Which script gives which table (schema: `figtab-repo/DATA_CONTRACT.md`)

| result file | made by |
|---|---|
| `price.csv` (E1/E3: price per target, rule, incumbent mode, B, unit; solver, optimality gap, verification flag) | `run_e1_*.py` -> `make_results.py price` |
| `frontier.csv` (breadth-depth frontier C(k)) | `run_frontier.py` -> `make_results.py frontier` |
| `m_effect.csv`, `m_effect_fit.csv` (E2, R4) | `run_e2_*.py` -> `make_results.py m_effect`, `analysis/r4.py` |
| `paired.csv`, `rule_order.csv`, `verdicts_e1.csv`, `verdicts.csv`, `r1_detail.csv`, `headline.json` (R1-R3, R5) | `analysis/run_analysis.py`, `run_r1.py`, `analysis/verdicts.py`, `analysis/headline.py` |
| `units.csv`, `units_tau.csv` (R5) | `run_units.py` -> `analysis/units.py` |
| `predictors.csv` (E4, R3; held-out board) | `analysis/predictors.py` |
| `price_magnitude.csv` (share already first; median, quartiles and cluster CI of the depth over targets not yet first; all caps, both incumbents; no geometric mean) | `analysis/magnitude.py` |
| `predictors_norm.csv` (R3 transfer on normalised quantities: price per task, in task-sd units for the score rules, and with an m term; reported variants, the raw-unit R3 stays the verdict) | `analysis/predictors_norm.py` |
| `e6b_confidence.csv`, `e6b_curve.csv` (E6 on a wider margin grid and with the margin from the boosted plan's sd) | `scripts/run_e6b.py`, `analysis/e6b.py` |
| `predictors_within.csv` (R3 within board: grouped cross-validated R^2 of log price on the gap, by board and rule; the transfer test stays the R3 verdict) | `analysis/predictors_within.py` |
| `flip_profile.csv`, `flip_summary.csv`, `flip_proxy.csv`, `flip_N.csv` (R1 diagnostic, descriptive: deficit-profile quantities per target and board, R1 breadth at c=1, proxy breadth from the profile, plurality margin vs number of models) | `analysis/flip.py` (needs `results/r1_*.csv`) |
| `predictors_hl.csv` (H-L, exploratory: deficit-profile features on top of the gap; fit board -> test board and leave-one-family-out) | `analysis/hl.py` |
| `bx_curve.csv`, `bx_crossing.csv` (crossing budget B_x of the median-type vs mean-type breadth/cost ordering; sigma and points units) | `run_r1.py` (c grid, `r1x_*.csv`) -> `analysis/bx.py` |
| `calibration.csv`, `calibration_summary.csv` | `run_calibration.py` |
| `e5_summary.csv`, `e6_*.csv`, `e7_*.csv`, `spillover_*.csv` (appendix; not in the figtab contract) | `run_e5.py`/`analysis/e5.py`, `run_e6.py`/`analysis/e6.py`, `run_e7.py`/`analysis/e7.py`, `analysis/spillover.py` |
| `solver_check.csv` | `run_checks.py` + the solver-size log of the price runs (`make_results.py solver_check`) |
| `boards.csv` | `make_results.py boards` |

Every table has a `<name>.meta.json` sidecar (script, git commit, data snapshot, seed, creation time).

## Solver notes (what "exact" means here)

Mean, z-mean, hierarchical mean: closed-form knapsack / water-filling. Minimum, quantile rules, odd-m median: sorting (exact). Even-m median with linear cost: DP over breakpoints; with convex
cost: a continuous threshold search, certified only to a numerical tolerance (see the comment in `lbprice/solvers.py`; `tol` = 0.002 in the E2 runs), not to the exact optimum. Plurality: MILP over the winner set. Borda (= mean win rate): level MILP with lazily added
per-rival constraints. Copeland (gamma = 1): MILP; for gamma other than 1 only a chord approximation is available and is labelled as such. Geometric mean is not solved (dropped from the study).
Every plan returned by any solver is re-checked with `lbprice.rules.is_first` (flag `verified` in `price.csv`); the MILP rules record the relative optimality gap reached (`opt_gap`; MIP gap 1e-9; per-solve time limit 30 s in E1, `tl` in the run script).
Brute-force verification: see `solver_check.csv` and `tests/` (instance counts and largest size per rule class are listed there).

## Compute actually used

CPU only (HiGHS MILP through `scipy.optimize.milp`, single-threaded per process; sandbox/job limit 2 CPUs, 4 GB). Measured:
- E1/E3 solver time (sum of per-solve seconds in the raw files): HELM 8,650 s (two shards; largest single solve 131 s), OLLB benchmark level 369 s, OLLB sub-task level 6,499 s (largest single solve 202 s).
- E2 sigma-unit run on the full HELM board (79 targets, 7 rules, 3 budgets): one process, about 4.3 h wall-clock.
- R1 on the top-30 targets: three shards per board, each roughly 10-30 min wall-clock; the c-grid for B_x (7 extra budgets per target, 10 targets per HELM / OLLB-m39 shard) about 5-15 min per shard.
- The statistical analyses (cluster bootstraps, 2000 draws) take minutes each; `analysis/hl.py` about 1 min at 2000 draws.
Wall-clock numbers other than E1 and E2 are read from the job log of the world's scheduler and are approximate; the raw CSVs carry no timing for them.
