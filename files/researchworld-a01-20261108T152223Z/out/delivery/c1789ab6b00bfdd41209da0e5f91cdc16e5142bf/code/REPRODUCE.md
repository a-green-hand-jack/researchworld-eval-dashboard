# Reproduction notes — minimum targeted investment to top a multi-task leaderboard

Everything under `code/` of the delivery is the repository `experiment-repo` (same layout; paths below are relative to `code/`).
All numbers in the paper's results come from the CSVs in `results/` and the tables derived from them in `results/tables/`; none is typed by hand.

## 1. Environment
Python 3.11.2, numpy 2.4.6, scipy 1.17.1 (HiGHS MILP via `scipy.optimize.milp`), pandas 3.0.6, pyarrow 26.0.0, pytest 9.2.0. CPU only; no GPU. Solvers are deterministic; all randomness is seeded (§4).
Network is needed only for `sh run.sh data` (the processed matrices are committed, so the experiments run offline).

## 2. Data (public snapshots, checksums)
| Dataset | Source / snapshot | Checksum | Licence / terms |
|---|---|---|---|
| Open LLM Leaderboard v2 `contents` | Hugging Face dataset `open-llm-leaderboard/contents`, commit `9c09a7cae43334062a82cb164f2ef255013dafa2`, file `data/train-00000-of-00001.parquet` (`src/fetch_ollb.py`) | sha256 `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5` | The dataset card declares no licence; public data. We redistribute only the derived score table `data/processed/ollb6.csv` (scores and the leaderboard's metadata columns). Per-model licences are in its `Hub License` column. |
| HELM MMLU v1.13.0 | `gs://crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/` (public bucket; `src/fetch_helm.py`) | per-file sha256 in `data/processed/helm_v1.13.0_manifest.sha256.json`; manifest hash `830bdb10a5518c50689d60c86623cc3d79ff5317d7e6b96408ea7dc2058de12b` | HELM is open source (Apache-2.0 code); the data are public result summaries, redistributed only as the derived table `data/processed/helm_mmlu57.csv`. |

Processing (`src/build_data.py`, `src/ollb_items.py`): OLLB — 4576 rows, 79 duplicate `fullname` rows dropped (best average kept), 4497 kept after deduplication; 4496 remain after the rows with `Flagged = True` are excluded at load time. The six task columns (IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO) are the Leaderboard's own normalised scores (random-baseline rescaling; for four tasks equal to 100(raw−floor)/(1−floor), for BBH and MUSR normalised per sub-task by the Leaderboard — do not re-derive them with a single floor). Raw scores ×100 (`ollb_raw`) are used for the raw-vs-normalised comparison. HELM — 79 models with all 57 MMLU subjects (EM, ×100). Dataset variants: `ollb` (all non-flagged), `ollb_nomerge` (also excluding merged models), `ollb_top500` (top-500 by mean), `ollb_raw`, `helm`. Data files `data/processed/*.csv` hash (sha256, first 16 hex): `ollb6.csv 3bf058715d37613b`, `helm_mmlu57.csv fae6683b2e42d4b0`, `helm_mmlu_neval.csv cf6541fb37814fdf`.

## 3. Commands
Run from the directory containing `run.sh`. Each target is independent (they were run as parallel jobs); do **not** edit `run.sh` while a target is running.
```
sh run.sh data        # network: download both snapshots, verify, rebuild data/processed
sh run.sh tests       # solvers vs brute force / LP / SLSQP (pytest, ~1.5 min)
sh run.sh example_plan  # L1-minimising plan of the HELM model ranked 5 (mean), gain10, five rules -> results/example_plan{,_summary}.csv (seconds)
sh run.sh theory      # real-data checks of the closed forms and MILPs -> results/theory_checks.csv
sh run.sh helm_main helm_pow                       # HELM grids (main_*: 6 caps x 14 rules x 79 targets)
sh run.sh ollb_score ollb_wmean                    # OLLB, score rules, all 4496 targets x 8 caps
sh run.sh ollb_ord_ceil ollb_ord_front0 ollb_ord_gain10 ollb_ord_emp95   # OLLB rank rules, 57 targets (head-20 + 40 log-uniform ranks; 57 distinct non-first targets)
sh run.sh ollb_top500_a ollb_top500_b ollb_top500_c ollb_top500_cope_ceil   # top-500 slice, 116 sampled targets: every rule incl. trimmed mean; Copeland on gain10 (116 targets) and ceil (30 targets) only; 8 caps in total
sh run.sh ollb_variants_score ollb_variants_ord    # no-merge and raw-score variants (C6): raw scores at ceil, front0, gain10, gain20
sh run.sh noise_helm noise_ollb taskboot tasksub   # robustness (C3, C7)
python3 src/analyze.py                             # all tables in results/tables/
sh run.sh all                                      # everything sequentially
```
Measured wall-clock per target on the shared research host (one job = 2 CPUs, host oversubscribed, so single-job times on an idle machine will be shorter): tests ~1.5 min; theory ~2 min; `helm_main` 71 min (Borda and Copeland MILPs dominate); `helm_pow` 4 s; `ollb_score` 146 min (4496 targets x 8 caps x 9 rules); `ollb_wmean` 98 min; `ollb_ord_ceil` 31, `_front0` 29, `_gain10` 10, `_emp95` 13 min; `ollb_top500_a` 16 min, `_b` 69 min (Copeland at gain10 dominates: 58 min), `_c` 35 min, `_cope_ceil` 14 min; `ollb_variants_score` about 160 min (no-merge) + 25 min (raw); `ollb_variants_ord` 140 min; `noise_helm` ~30 min (R = 100); `noise_ollb` ~12 min (R = 50); `taskboot` ~15 min; `tasksub` ~5 min; `analyze.py` ~8 min. The sum of job wall-clock times is about 15 hours (the jobs ran concurrently, about 3.5 h elapsed), i.e. more than the 4 CPU-hour guidance of the task; the scale-down options (sampled targets for rank rules on OLLB, Copeland only on two caps of the top-500 slice, raw scores on four caps) are what kept it at that. The HELM grids (the main results) take about 75 min on their own.

## 4. Seeds and conventions
- Target sample for rank rules on OLLB: `src/run_core.py` target set `sample` = the 20 best-ranked models plus `--nsample` models at log-uniform ranks (deterministic, no RNG); `topK` = K best.
- Noise Monte Carlo (`src/run_robust.py noise`): seed 0, R = 100 draws (HELM) / 50 (OLLB top-500), targets = the 10 models ranked 2..11 by the observed mean, cap gain10. Draw 0 is already a noisy draw; the observed data are not a draw (observed rank in `rank_mean_obs`). SE per cell: binomial with the benchmark's item count (`data/processed/ollb_noise.json`, `helm_mmlu_neval.csv`), clipped to [0,100].
- Task bootstrap (`taskboot`): seed 0, R = 100, resampling the 57 subjects with replacement, same targets. Task-subset scaling (`tasksub`): seed 0, n ∈ {3, 6, 12, 24, 48} random subsets of subjects, 60 draws each, targets at rank 2 and 5 under the rule.
- Weighted-mean rules `wmean0..4`: weights Dirichlet(1,…,1) from `numpy.random.default_rng(1000 + k)`.
- Bootstrap CIs in `results/tables` (`src/analyze.py`): seed 0, B = 1000, resampling targets.
- Margin ε = 10⁻³ score points: "first" means strictly above every other model under the rule by that margin (ties are not first). MILPs use `mip_rel_gap = 0`; a solver time limit or numerical failure is stored as NaN and reported as a `failed` share, never as "infeasible"; infeasible (cap too low to reach first) is `inf`.

## 5. Result files and what they feed
Columns of the grid files (`helm_main.csv`, `ollb_*.csv`): dataset, cap, rule, target, target_idx, rank_mean (rank under the mean), rank_rule, gap (target's shortfall to the rule's leader), L1 (total points raised), K (tasks touched), Linf (largest single jump), K_at_L1 (tasks touched by the L1-optimal plan), L1_lexK (smallest L1 among plans touching K tasks). Cap scenarios: `ceil` (100), `front0/front2` (best other score on each task + 0/2), `gain5/10/20` (+h on each task), `emp95/emp99` (95th/99th percentile of fine-tune-minus-base differences per task over the OLLB base/fine-tune pairs).

| Claim | Files | Table (`results/tables/`) |
|---|---|---|
| C1 rule dependence, stability of order | `helm_main`, `helm_pow`, `ollb_score`, `ollb_wmean`, `ollb_ord_*`, `ollb_top500_*` | `main_by_rank` (median K/L1/Linf, bootstrap CI, infeasible share per rule × cap × rank bin), `vs_mean`, `rule_order_stability`, `cost_vs_gap`, `rank_scaling` |
| C2 mean closed form | `theory_checks.csv` (T1, T2) | — |
| C3 median/min force K ≈ n/2 and n; K–n scaling | `helm_tasksub_{gain10,ceil}`, `theory_checks.csv` (T4) | `tasksub_summary` (with closed-form `K_bound`) |
| C4 caps and feasibility | all grids | `main_by_rank` (`infeasible` column = feasibility complement) |
| C5 rank rules vs score rules | `helm_main`, `ollb_ord_*`, `ollb_top500_*` | `main_by_rank`, `vs_mean` |
| C6 raw vs normalised | `ollb_score` vs `ollb_raw_score`, `ollb_nomerge_*` | `raw_vs_norm` |
| C7 evaluation noise, task bootstrap | `helm_noise_gain10`, `ollb_noise_gain10`, `helm_taskboot_gain10` | `noise_summary_*`, `taskboot_summary_helm` |
| What a plan looks like (C1/C5) | `example_plan.csv`, `example_plan_summary.csv` (HELM, rank-5 target, gain10; optimal plans are not unique, see `src/example_plan.py`) | — |
| Solver validation | `theory_checks.csv`, `tests/` | — |

`theory_checks.csv`: T1–T4, T6 use 60 random targets (seed 0) per (dataset, cap) on the full real matrix, T5 compares the MILPs for Borda, Condorcet and plurality with exhaustive enumeration on 40 random real-data subsamples of 6 models × 4 tasks. Copeland is validated against brute force in `tests/test_ordinal.py`. Figures and LaTeX tables are produced by the `figures/scripts` and `tables` of the delivery from these files (`*.inputs.json` there record the input files).

## 6. Reading the tables
`results/tables/main_by_rank.csv` has two kinds of cost columns. `X_med/X_lo/X_hi` (X = K, L1, Linf, L1_over_sd, K_at_L1, L1_lexK) is the median over **all** targets with infeasible targets entered as +inf (so it is `inf` when more than half are infeasible); `X_med_feas/X_lo_feas/X_hi_feas` is the median and 95% bootstrap CI over the **feasible** targets only, with the count `n_feasible`; `infeasible` and `failed` are shares (solver failures are excluded from both). Use the `_feas` columns as costs and always report `infeasible` beside them. `vs_mean.csv` is a paired ratio L1(rule)/L1(mean) over targets where **both** rules are feasible (`n_both_feasible`), with `n_only_rule_feasible` and `n_only_mean_feasible` counting targets feasible for one of the two. `results/FINDINGS.md` states the finding per claim with the table that supports it, including the negative ones (C3).

## 7. Method in brief
The target model raises its scores y_t ∈ [x_t, cap_t] on chosen tasks; every other model is fixed. Cost: L1 = Σ(y_t − x_t), K = number of tasks changed, Linf = max jump. Score rules (mean, geometric/harmonic/power mean, weighted mean, median, minimum): closed forms, water-filling (power means) or a greedy bound; trimmed mean and rank rules (Borda, Condorcet winner, Copeland, plurality): exact MILP with lazily generated rival constraints (`src/mti/scorerules.py`, `src/mti/ordinal.py`). Linf by bisection on the feasible uniform jump. Condorcet-winner cost is an upper bound for any Condorcet-consistent rule (if no Condorcet winner can be created at the cap, the target is reported infeasible for that rule).
