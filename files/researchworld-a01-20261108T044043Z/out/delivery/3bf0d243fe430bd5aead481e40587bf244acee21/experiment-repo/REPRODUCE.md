# Reproduction notes (analysis part)

Every number in a delivered CSV was produced by the shipped code from the pinned inputs below; the runtime measurements, the minimal path and
the solver-validity notes are in the sections that follow.
**Scope note.** The OLLB top-500 slice (`results/variants/var_ollb_top500.csv`, `results/summary/summary_variants.csv`) holds the mean, median, min, Borda, Condorcet-winner and plurality rules at `emp99` and `ceil`, and Copeland at `emp99` only
(the geometric, harmonic and power means are not in this slice); Copeland covers all 500 targets (6 MILP shards, 120 s limit per MILP and per cost). **Feasibility and the minimum L1 cost are different outcomes.**
The L1, K and Linf programs are solved separately, and a time-limited L1 solve (NaN) says nothing about feasibility. `results/variants/copeland_top500_screen.csv` (`code/copeland_screen.py`) settles feasibility per target:
a finite value of any of the three costs shows a feasible solution, an infinite one proves infeasibility, and the cap-saturated vector (monotone rule: a target is feasible iff it is strictly first with every task at its cap) decides the same way.
Result: **375 of 500 targets feasible, 125 infeasible** (374 of 499 excluding the mean leader), none undecided; the MILP and the saturated vector agree on all 500. For the **L1 minimum** the outcomes are
329 solved (finite), 121 proved infeasible and 50 L1-censored; of the 50, 46 are feasible (their K and Linf solves are finite; only the minimum L1 is unresolved) and 4 are infeasible (infinite K and Linf, the saturated vector loses). Per-stratum counts: `results/variants/copeland_top500_feasibility.csv`.
`feas_frac` in `summary_variants.csv` is the share of finite L1 costs, so for these rows it undercounts feasibility by the L1-censored feasible targets. Copeland was not run at `ceil` on the slice. The 120 s limit is wall-clock on a host shared with other jobs, so the censored count is probably higher than on an idle machine.

## Environment
Python 3.11.2, NumPy 2.4.6, SciPy 1.17.1 (HiGHS MILP/LP via `scipy.optimize.milp/linprog`), pandas 3.0.6, PyArrow 26.0.0, pytest 9.2.0.
CPU only (2 CPUs / 4 GB container, shared host, Xeon Gold 6230). No GPU, no network after the downloads.

## Data (public, no login)
| source | version | file / checksum | use |
|---|---|---|---|
| Open LLM Leaderboard `open-llm-leaderboard/contents` | dataset commit `9c09a7cae43334062a82cb164f2ef255013dafa2` (last updated 2025-03-20) | `data/train-00000-of-00001.parquet`, SHA-256 `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5` (`code/fetch_ollb.py` verifies it) | 4576 rows, 4497 distinct model names after dropping 79 duplicate names (best-scoring variant kept); 6 normalised task scores |
| HELM MMLU `crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0` | v1.13.0 (summary date 2025-01-10) | 303 files, per-file SHA-256 written by `code/fetch_helm.py`; manifest of manifests `830bdb10a5518c50689d60c86623cc3d79ff5317d7e6b96408ea7dc2058de12b` | 79 models x 57 subject EM scores (all 79 complete) |
| `open-llm-leaderboard/results` | commit `aa81ecc38fdc5708254b833923368970efdf5ef5`, one file (`0-hero/Matter-0.2-7B-DPO/results_2024-08-07T13-21-02.903091.json`, SHA-256 `c0386eb6b6b7ca3c6cc596b190dcd898b17fb7055b092229d00ff50727930856`) | item counts per task for the evaluation-noise model (`data/processed/ollb_noise.json`) |

The OLLB score used is the leaderboard's normalised score (`(raw - floor)/(1 - floor)`, floors solved from the data and stored in
`ollb_noise.json`); `Average` = mean of the six normalised scores and HELM `MMLU All Subjects - EM` = mean of the 57 subject EM values
(`results/official_rules_check.csv`: max deviation 1.4e-14 and 5.7e-14 points). HELM publishes no mean win rate in the downloaded
files. Evaluation noise uses binomial standard errors from the item counts (HELM: `# eval` per subject; OLLB: counts from the single
results file above, assumed equal for all models, a limitation).

**Licences.** Not declared by either source (HELM code Apache-2.0; `contents` has per-model `Hub License` column). We redistribute only
derived score tables (`data/processed/`: model x task matrices and metadata used) and not the raw downloads. Model names in the tables
are public leaderboard entries.

**Filters.** OLLB: duplicates of `fullname` dropped (best `Average` kept; 4497 distinct names), then the flagged model(s) removed (4496 models
analysed); merged and MoE models are kept in the main analysis. Robustness slices: `ollb_nomerge` (3789 models, merged models also removed),
`ollb_top500` (the 500 best models by the mean of the six normalised scores) and `ollb_raw` (raw, un-normalised task accuracies x 100; caps
there are `ceil`/`gain` only because the empirical gains are in normalised points). HELM: models with all 57 subjects (79 of 79).

## Seeds
All random draws use `numpy.random.default_rng(seed)` with seed 0 (`run_core.py --seed`, `run_robust.py --seed`, `run_weights.py
--seed`, `theory_check.py`, bootstrap in `summarize.py`). Solvers are deterministic (HiGHS, default settings; 120 s MILP time limit, a hit is
recorded as censored `NaN`).
**Exception (figures and tables, `figures/src/tables.py` in the report repository, not part of this analysis code):** its bootstrap intervals seed NumPy's default
generator with the first eight SHA-256 bytes of the input float-vector bytes, read as a little-endian integer; 2000 resamples, identical draws reused for identical
vectors. Analysis and figure sampling otherwise keep seed 0.

## Commands
`code/run_all.sh` runs everything in order (data -> tests/theory check -> core grid -> uncertainty -> variants -> tables). Every step
that produced a delivered table has a log in `results/logs/`; the logs listed under "Stale, empty or failed logs" below do not.

### Measured run time (shared 2-CPU container, Xeon Gold 6230; several of our jobs and other worlds' jobs ran at once)
Wall seconds per step are from the logs of the run that wrote the shipped file (job wall time on the shared host, so upper bounds on
an idle machine). CPU seconds (user + system) are measured only for the steps timed with `code/timed.py` and for the jobs of the
resource accounting of the last run; they are about 0.4-0.65 of the wall seconds because of the contention. CPU seconds of the
earlier jobs were not recorded and are not estimated here.

| step | wall s | CPU s |
|---|---|---|
| data layer (`fetch_ollb`, `fetch_helm`, `build_data`; `results/runtime_data_layer.csv`) | 403 | 20 |
| tests (`code/tests`) / theory check | 65 / 60 | 42 / 37 (`runtime_minimal_path.csv`) |
| OLLB primary caps, closed forms / OLLB cap sweep, closed forms | 138 / 773 | not recorded |
| OLLB ordinal top-50 (Borda, Condorcet, plurality) at `emp99` | 390 | 386 |
| HELM primary caps, 8 rules / HELM cap sweep (10 rules x 5 caps) / HELM Copeland (`emp99T`, `ceil`) | 518 / 3445 / 983 | not recorded |
| OLLB noise and task bootstrap, closed forms | 78 + 44 | not recorded |
| OLLB ordinal noise / task bootstrap (60 draws) | 3720 / 1581 | not recorded / 1133 |
| HELM noise / task bootstrap / task subsets | 3290 / 1169 / 189 | not recorded |
| OLLB variants `nomerge`, `raw` | 83, 37 | not recorded |
| OLLB top-500 ordinal rules, 2 shards (run in parallel) | 1821 + 2619 | 1601 + 1395 |
| margin variants (4 runs), eps = 1e-5 grid check (HELM + OLLB) | 228, 365 | not recorded, 226 (OLLB) |
| weights and sigma-unit cost steps (`results/runtime_unlogged_steps.csv`) | 82 | 47 |
| `code/make_tables.sh` (`results/runtime_make_tables.csv`) | 648 | 257 |
| **sum of the rows above** | **22,729 s = 6.3 h** | not complete |

Every row, with its source (a log line, `code/timed.py`, or the job accounting read when the job ended) and the log file, is in
`results/runtime_all_steps.csv`. For the steps marked as job accounting the timing is not in any file of this repository (their logs hold
no timing line) and it is not reproducible from the delivered files; it is reported as read then. The logs are delivered under `results/logs/`
(written by the job wrappers, `ht-resource run ... > results/logs/<step>.log`).

The sum is the total job time of the runs that wrote the shipped files, except the OLLB leaf-task run (about 16 min, below), the cap-evidence
and ordinal-sample steps below and the OLLB top-500 Copeland run (6 shards, wall 8,633, 10,564, 9,772, 13,059, 8,699 and 13,318 s run in parallel on the shared host, i.e. 13,318 s = 3.7 h elapsed; CPU seconds not recorded; logs `results/logs/copeland_ollb_top500_K.log`). Earlier attempts that were superseded (listed under "Stale, empty or
failed logs") are not in the sum, and their wall time is not accounted for here. Because the jobs share two cores, the sum of wall seconds is not the
time on an idle machine; an idle machine needs roughly the CPU seconds, about half of it for the steps measured.

### Minimal reproduction path (`code/run_minimal.sh`)
From the shipped `data/processed/` to the primary-cap grid (OLLB `emp99`, HELM `emp99T`; six score rules and, on OLLB top-50 and HELM,
Borda/Condorcet/plurality), the feasibility frontier, the paired rule comparisons and the rank-stratum summaries behind F1-F3 and
T2-T4, with the tests and the theory check, no robustness or variant runs and no Copeland:
`bash code/run_minimal.sh` (writes only under `results_min/`, per-step times in `results_min/times.csv`). Measured (shared host, this
run): **996 s wall = 16.6 min, 565 CPU s = 9.4 CPU-min** (`results/runtime_minimal_path.csv`: tests 65 s, theory check 60 s, OLLB
closed forms 443 s, OLLB ordinal top-50 330 s, HELM 48 s, assembly and summaries 51 s). `code/check_minimal.py` compares its tables with
the shipped `results/core_*.csv`: 0 differences over 27,126 OLLB and 632 HELM rows for K, L1 and Linf (max |diff| 1e-7, MILP gap);
output `results/logs/minimal_path.log`. The full set (everything above) is `bash code/run_all.sh`.

### OLLB leaf-task run (request #8)
`results/leaf/README.md` gives the gate, the file rule, the normalisation check and the reading rules. Steps (jobs): `python3
code/fetch_ollb_leaves.py RAW 500` (network, ~5 min) and `python3 code/build_ollb_leaves.py RAW data/processed/ollb_leaves.csv
results/ollb_leaves_gate.json` (the shipped CSV is its output); `bash code/run_leaf.sh {closed_leaf,closed_six,ord_leaf,ord_six}` (job
wall 22 s, 26 s, 602 s, 311 s on the shared host; CPU 3, 9, 266, 165 s from the resource accounting; logs `results/logs/leaf_*.log`);
`python3 code/assemble_leaf.py`; `python3 code/leaf_provenance.py RAW` writes the source manifest, selected-file manifest and digests (a second retrieval, with 429 back-off, reproduced `leaves.jsonl` byte for byte: SHA-256 `5e350318579736d67c0b64210aa173388bb3720101e86685634b0de92e175905`). The 39 are the leaderboard's score components, not disjoint subtasks: the three GPQA components (diamond, main, extended) are nested, overlapping variants (see `results/leaf/README.md`).

### Cap evidence (request #10) and ordinal full-board sample (request #11)
`python3 code/cap_evidence.py results/cap_evidence` (seed 0, 1000 pair-bootstrap draws; 18 s wall on one CPU; documented in `results/cap_evidence/README.md`):
pair bootstrap of the 540 fine-tune/base pairs, leave-one-task-allowance-out, descriptive joint gains, HELM uniform-allowance sensitivity; asserts that its
cap-saturated feasibility test reproduces the feasible counts of the primary runs (`core_ollb.csv` emp99, `core_helm.csv` gain5/10/20).
`python3 code/ordinal_sample.py ... --shard K/4` (K = 0..3) and `python3 code/summarize_ordinal_sample.py` (60 rank-stratified targets beyond rank 50, Borda and
Condorcet, `emp99` and `ceil`; documented in `results/ordinal_sample/README.md`; shard wall times 268, 439, 293 and 295 s on the shared host, logs
`results/logs/ordinal_sample_K.log`); memory-lean solver `code/mti/ordinal_lean.py`, checked against the dense solvers by `code/tests/test_ordinal_lean.py`
(56 s).

### Stale, empty or failed logs
Kept for provenance, not read by any script, and not used for a shipped table:
- `results/logs/helm_main.log`, `results/logs/helm_closed.log`, `results/logs/ollb_closed.log`: earlier attempts of the core grid; the shipped core tables
  are assembled only from `results/runs/` (the `SRC` list of `code/assemble_core.py`), written by the `*_primary_*`, `*_capsweep_*` and
  `copeland*` steps whose logs are present.
- `results/logs/helm_taskboot.log`: failed at start (old path `src/run_robust.py`); the step was rerun as `rob_helm_taskboot_emp99T.log`.
- `results/logs/step6.log`: failed at start (script of an earlier layout no longer exists); superseded by the `var_*` and margin steps.
- `results/logs/weights.log`, `results/logs/zcost.log`, `results/logs/ollb_ordinal.log`: empty (output went to the CSVs only). The weights and sigma-unit cost
  steps were rerun under `code/timed.py` (`code/rerun_unlogged.sh`, log `results/logs/rerun_unlogged.log`, times in
  `results/runtime_unlogged_steps.csv`): all six `results/variants/{weights,zcost}_*.csv` were reproduced identically. The earlier
  estimate of "10-30 min each" in this file was wrong; they take 6-24 s each. `results/logs/ollb_ordinal.log` is superseded by
  `results/logs/ollb_primary_ordinal_top50.log`.
- `results/logs/var_ollb.log`: its OLLB top-500 part is superseded by the sharded reruns `results/logs/var_ollb_top500_{0,1}.log` and
  `results/logs/copeland_ollb_top500_*.log` (after the 1e-9 rounding of OLLB scores, see below).

## Validity of the solvers and of the cost measures (what the checks support)

**Problem solved.** The target raises its scores `y_t in [x_t, c_t]` (cap `c_t`), everything else fixed, and must be *strictly first*.
For score rules (mean, power means, median, min, trimmed mean, weighted mean) the optimum is a closed form / exact LP / bisection and
"strictly first" means a lead of at least `eps = 1e-3` points. For the rank rules (Borda, Condorcet winner, plurality, Copeland) the
outcome depends only on which rivals the target ties (level `= s`, half credit) or passes (level `>= s + eps`) on each task, so the
exact MILPs (`code/mti/ordinal.py`) optimise over the finite level grid `{s, s + eps : s a rival's score on that task}`.

**Claim 1 (finite grid, not an infimum).** The ordinal optimum is exact for the *margin-`eps` problem* (passing a rival requires
`y >= s + eps`, ties count 1/2 exactly). It is not claimed to equal the infimum of the open strict-win problem. The grid is no
restriction for the margin problem: the outcome is monotone in each `y_t` (a higher level only passes or ties more rivals, which can
only raise the target's points and lower rivals' points), so between two rival scores the cheapest level is the lower one, which the
grid contains. Relation to the continuous strict problem: a strict-win plan can be rounded up to the grid at an extra cost of at most
`eps` per raised task, so `inf(continuous) <= grid optimum <= inf(continuous) + n_raised * eps`, **unless a cap lies within `eps` above
a rival score that the plan must pass** (the level `s + eps` is then not available). `test_grid_is_within_n_eps_of_continuous_infimum`
in `code/tests/test_ordinal.py` checks the bound on random real-valued instances (slack caps). `code/eps_check.py` checks it on the
data, margin `1e-5` against the core `1e-3` (`results/eps_grid_check.csv`; HELM: all 79 targets x Borda / Condorcet / Copeland /
plurality at `emp99T`; OLLB: the 50 best targets x Borda / Condorcet / plurality at `emp99`): no feasibility change in any of the 7 blocks,
`K` changes for 1 target (OLLB Borda), `L1` rises by at most 0.055 points on HELM (bound `57 eps = 0.057`) and by at most 0.6% of the cost
on either dataset; 4 OLLB Borda targets exceed the bound `6 eps` (largest 0.105 points, the cap-edge case). `Linf` does not depend on
`eps` (bisection on strict comparisons, tolerance 1e-6; it differs by <= 4e-16 between the two margin runs).

**Plurality margin.** Plurality credits are rationals (a first place shared by `m` models gives `1/m`); the MILP requires the target to
exceed each rival by `1e-4` credit. At most 4 models tie for first on a HELM task (2 on OLLB), so credit totals differ by multiples of
1/60 (HELM) or 1/6 (OLLB) when the target joins them: the 1e-4 is below every real difference and above the solver tolerance (1e-6).
It is a numerical-strictness device, not a second margin on scores; the score crossing grid is the same `eps = 1e-3`.

**MILP optimality gap.** HiGHS stops at a relative MIP gap of 1e-4 (default, not changed), so a returned ordinal cost can exceed the
optimum by up to that fraction (the grid test above needs a 2e-4 tolerance for this reason). Re-solving 44 HELM (4 rules x 11
targets, `ceil`) and 12 OLLB top-500 (4 rules x 3 targets, `ceil`) instances with the gap set to 0 returned identical costs
(`|diff| <= 4e-16`) without extra time. Runs that hit the 120 s limit are `NaN` (censored), never counted as infeasible.

**Exact ties on OLLB (data-load fix).** The leaderboard's normalised scores of models with the same raw accuracy differ by float noise
(~1e-15; 284 such pairs on MATH Lvl 5, GPQA and MUSR). `code/mti/data.py` now rounds scores to 1e-9 so these are exact ties for the rank
rules. All OLLB runs that contain a rank rule were redone on the rounded data (top-50 core runs, top-500 slice, ordinal task bootstrap);
the evaluation-noise draws break every tie by construction and were not redone; HELM has no near-ties (smallest gap 0.377 points).
`results/rounding_check.csv` compares old and new runs: no feasibility change anywhere; top-50 core runs: no `L1` change above 3e-9; ordinal
task bootstrap: 3 of 1260 `L1` values change (by 0.001) and one value that hit the time limit in the old run is solved in the new one; top-500 slice: 3 of 500 Borda costs change at each cap (largest 0.10 points) and
9 of the 3000 ordinal `Linf` values (largest 2.0 points, one Condorcet target at `emp99`). Score-rule results are unchanged to 1e-7
points (`code/check_minimal.py`).

**Linf is a cap-saturated uniform lift, not a literal uniform raise.** For every (monotone) rule the `Linf` column is the smallest `d`
such that moving *every* task to `min(x_t + d, c_t)` makes the target strictly first; any plan whose largest raise is `<= d` is
dominated by that saturated lift. Where caps bind, tasks with headroom `c_t - x_t < d` move by less than `d`, so the real cost of the
lift is `L1_unif = sum_t min(Linf, c_t - x_t)` (and `K_unif` = number of tasks with headroom), not `n * Linf`. `code/uniform_lift.py`
computes both against the optimum per target (`results/summary/uniform_vs_optimal_{ollb,helm}.csv`: medians by rank stratum with
bootstrap intervals, share of targets with a binding cap, `L1_unif / L1_opt`, `K_unif / K_opt`, `Linf / (L1_opt / n)`; per target in
`*_targets.csv`). For the mean the saturated lift costs exactly the optimum in L1 (ratio 1.000: the same total points) but touches every
task with headroom (`K` ratio 1.5-3.6); for min, median and the rank rules it is several times dearer (see the files for each cap).

## Script -> table / figure
| output | script | claim it supports |
|---|---|---|
| `results/core_{ollb,helm}.csv` | `code/run_core.py` (+ `code/assemble_core.py`) | minimum investment (K, L1, Linf) to be strictly first by cap x rule x target (F1-F3, T3) |
| `results/theory_check.csv` | `code/theory_check.py` (`code/mti/theory.py`) | P1-P3 closed forms equal the exact solvers (T2) |
| `results/official_rules_check.csv` | `code/official_rules_check.py` | the mean we use is the sites' published aggregate |
| `results/robust/*`, `results/summary/summary_rob_*` | `code/run_robust.py`, `code/summarize_robust.py` | intervals: evaluation noise, task resampling, number of tasks (F4, F5) |
| `results/summary/frontier_*.csv` | `code/frontier.py` | feasible share by initial-rank stratum and largest initial rank that can reach first, with bootstrap CIs (F3, T3) |
| `results/summary/paired_*.csv` | `code/paired.py` | rule-vs-rule cost ratios on the targets feasible under both rules, with counts |
| `results/summary/summary_*_groups.csv`, `summary_variants.csv` | `code/summarize.py`, `code/summarize_variants.py` | medians by rank stratum with bootstrap CIs; variant-vs-baseline comparisons |
| `results/variants/*` | `run_core.py`, `run_weights.py`, `run_zcost.py` | robustness to slice, scale, margin, weights, cost scale |
| `results/summary/uniform_vs_optimal_*.csv` | `code/uniform_lift.py` | cost of the saturated uniform lift that the Linf cost describes, against the L1 optimum |
| `results/eps_grid_check.csv`, `results/variants/eps1e5_*.csv` | `code/eps_check.py`, `run_core.py --eps 1e-5` | the grid margin does not drive the rank-rule results |
| `results/rounding_check.csv` | `code/mti/data.py` rounding (1e-9) rerun | float-noise ties on OLLB change results negligibly |
| `results/runtime_*.csv` (all steps: `runtime_all_steps.csv`), `results/logs/minimal_path.log`, `results/logs/rerun_unlogged.log` | `code/timed.py`, `code/run_minimal.sh`, `code/rerun_unlogged.sh`, `code/check_minimal.py` | measured run time and the minimal path |
| `results/variants/var_ollb_top500.csv` | `code/run_core.py --shard`, `code/merge_shards.py` | OLLB top-500 slice, shards merged (Copeland rows included) |
| `results/variants/copeland_top500_screen.csv` | `code/copeland_screen.py` | settled Copeland top-500 feasibility per target (MILP statuses of L1/K/Linf and the cap-saturated vector); `copeland_top500_feasibility.csv` holds the per-stratum counts |
| `results/leaf/*`, `data/processed/ollb_leaves.csv`, `results/ollb_leaves_gate.json` | `code/fetch_ollb_leaves.py`, `code/build_ollb_leaves.py`, `code/run_leaf.sh`, `code/assemble_leaf.py` | 39 score components (overlapping GPQA variants) vs the six published tasks of the same 499 models (scaling check on OLLB) |
| `results/cap_evidence/*` | `code/cap_evidence.py` | uncertainty and sensitivity of the empirical gain caps: pair bootstrap, leave-one-task-allowance-out, joint gains, HELM allowance sensitivity (request #10) |
| `results/ordinal_sample/*` | `code/ordinal_sample.py`, `code/summarize_ordinal_sample.py`, `code/mti/ordinal_lean.py` | Borda/Condorcet beyond the top 50 on the full OLLB board, rank-stratified sample (request #11) |
| `results/leaf/source_*.{csv,json}`, `results/leaf/selected_files.csv` | `code/fetch_ollb_leaves.py`, `code/leaf_provenance.py` | source files, checksums and selected files of the leaf retrieval (request #9) |
| tests | `code/tests/` | each solver equals brute force / an independent LP on small random instances |

## Forbidden-material record
The task forbids searching for or reading the published paper on this question or anything citing or discussing it. During this
work (analysis position): nothing of that kind was searched for or encountered. Only the pinned datasets above and their cards/URLs
were accessed.
