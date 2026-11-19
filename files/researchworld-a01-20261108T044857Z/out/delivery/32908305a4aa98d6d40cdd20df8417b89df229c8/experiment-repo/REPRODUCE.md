# Reproduction notes (analysis part)

Every number in a delivered CSV was produced by the shipped code from the pinned inputs below. `code/run_all.sh` lists every run in order;
it has **not** been run end to end as one script (runs were launched as separate jobs, some sharded, on a shared host); the per-run
times below are those measured jobs. Results files are regenerated in place by the same commands (same seeds).

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

## Commands and run times
`code/run_all.sh` lists every step in order (data -> tests/theory check -> core grid -> uncertainty -> variants -> tables); each line is
one job. **`run_all.sh` itself was not run end to end:** the delivered files were produced by running its steps as separate
`ht-resource run local-compute` jobs (several in parallel on the shared 2-CPU container, so wall-clock is inflated by sharing), and
three later fixes were applied by re-running only the affected steps (see below). Wall-clock measured for the steps that were timed
(from the job records; an unlisted step was not timed):

| step | measured wall-clock |
|---|---|
| `code/tests/test_ordinal.py` (6 tests, pytest) | about 35 s |
| HELM cap sweep, 10 rules x 5 caps incl. Copeland (`helm_capsweep`) | about 2200 s |
| OLLB top-500 slice, Borda/Condorcet/plurality (`top500`) | 3600-4900 s |
| OLLB ordinal evaluation noise / task bootstrap (`rob_ollb_*_ord`, 60 draws) | 3300-4500 s each |
| OLLB top-500 Copeland, 6 shards in parallel (`--shard i/6`) | about 3 h wall-clock for the slowest shard |
| censored top-500 Copeland rows, 900 s MILP limit, 14 jobs of 3 targets (`rerun_censored_copeland.sh`) | about 8-31 min per job, 14 jobs in parallel |
| plurality-only reruns (`rerun_plurality.sh`, 12 jobs) | 1-4 min each |
| `code/make_tables.sh` (core assembly, summaries, frontier, paired comparisons, uniform baseline) | 5 min 18 s |

Steps not in the table (data preparation, closed-form OLLB grid, HELM primary/Copeland, HELM noise and bootstraps, survival, cap
bootstrap, margin/weights/sigma-unit variants) were run as parallel jobs that each took minutes to well under an hour; their individual
times were not recorded and no total is claimed.

**Censoring and reruns.** A MILP that hits the 120 s limit is recorded as censored `NaN`. In the OLLB top-500 Copeland run 42 of 500
targets were censored at 120 s; `code/rerun_censored_copeland.sh` re-solved exactly those targets with `run_core.py --time-limit 900`
and `code/merge_censored.py` replaced the rows, leaving 0 censored of 500 (`variants/var_ollb_top500_copeland.csv`; raw reruns in
`rerun_censored/`). All ordinal fixes (strict model, plurality exactness) were applied to the delivered files either by a full rerun
of the affected file or, for plurality only, by `code/rerun_plurality.sh` + `code/patch_rule_rows.py` (valid because draws and
targets do not depend on the rule list; the patch asserts matching row counts).

## Ordinal rules: what is exact (revised after review, `experiment-repo`#6)
Borda, Condorcet requirement, plurality and Copeland use plain strict comparisons (win: strictly higher score; equal: tie 1/2; first:
strictly largest total) and no margin; `eps` is only the granularity of the witness raise, so margin variants are not defined for them.
Feasibility, `K` and `Linf` are exact for continuous raises. `L1` is the cost of an explicit witness (each raised task at a rival's score or
at most `eps` above it, capped); the infimum lies in [`L1` - n*eps, `L1`], n = number of tasks. Plurality is solved on the integer lattice of
its credits (no arbitrary lead threshold) and every witness is re-checked in exact rational arithmetic; Borda/Condorcet/Copeland totals are
half-integers. Tests: `code/tests/test_ordinal.py` (integer brute force; real-valued adversarial brute force with fractional ties and caps
off the grid; the reviewer's examples). `results/audit_ordinal_fix.csv` lists, per file and rule, how many rows changed relative to the first delivery.

## Map: paper label -> script -> inputs
Figure and table scripts live in `figures/src/` of `figtab-repo` (full command lines and per-output sidecars: `figures/MANIFEST.md`);
`R` = this repository's `results/`. Labels are those of `paper/main.tex` at the time of writing.
| paper label | output | produced by (`figtab-repo`) | analysis files it reads (`R/`) |
|---|---|---|---|
| `fig:main` | `F_ollb_primary`, `F_helm_primary` | `fig_rank_rules.py` | `core_ollb.csv` (cap emp99), `core_helm.csv` (emp99T) |
| `tab:T4` | `T4_frontier_{ollb,helm}.tex` | `tables.py` | `core_*.csv`, `summary/frontier_*.csv` |
| `tab:T3` | `T3c_rules_{ollb_emp99,helm_emp99T}.tex` | `tables_v2.py` | `core_*.csv`, `summary/paired_*.csv` |
| `tab:T2` | `T2_theory_check.tex` | `tables.py` | `theory_check.csv` |
| `fig:oracle` | `F_{ollb,helm}_oracle` | `fig_rank_rules.py --caps ceil` | `core_*.csv` (cap ceil) |
| `fig:capgrid`, `fig:capgridh` | `F_ollb_capgrid`, `F_helm_capgrid` | `fig_cap_grid.py` | `core_*.csv` (all caps) |
| `fig:scaling` | `F_helm_scaling` | `fig_scaling.py` | `summary/summary_rob_helm_tasksub_emp99T.csv` (own-rule targets); `summary_rob_helm_tasksubcommon_emp99T.csv` and the `*_feasible_counts.csv` files (common-target run) |
| `fig:robust` | `F_robust` | `fig_robust.py` | `summary/summary_rob_*.csv`, `core_*.csv` |
| `tab:T5` | `T5_exceptions_{ollb,helm}.tex` | `tables_v2.py` | `core_*.csv`, `summary/paired_*.csv` |
| appendix `app:more` (variants) | numbers quoted from the file | -- | `summary/summary_variants.csv` (`code/summarize_variants.py`), `variants/*` |
| `app:ordinal` | exactness statement above | -- | `audit_ordinal_fix.csv`, `code/tests/test_ordinal.py` |
| cap uncertainty (text) | numbers quoted from the file | -- | `summary/summary_capboot_{ollb,helm}.csv` (`code/capboot.py`) |
| fixed-policy survival (text) | numbers quoted from the file | -- | `robust/survival_{ollb,helm}_emp99.csv` (`code/run_survival.py`; `code/mti/policies.py`) |
| uniform-raise baseline (text) | numbers quoted from the file | -- | `uniform_baseline_{ollb,helm}.csv`, `summary/summary_uniform_baseline_*.csv` (`code/uniform_baseline.py`) |
Analysis script -> result file (what each file is made of):
| output | script | claim it supports |
|---|---|---|
| `core_{ollb,helm}.csv` (from `runs/`) | `code/run_core.py` (+ `assemble_core.py`; shardable) | minimum investment (K, L1, Linf) to be strictly first by cap x rule x target |
| `theory_check.csv` | `code/theory_check.py` (`code/mti/theory.py`) | closed forms equal the exact solvers |
| `official_rules_check.csv` | `code/official_rules_check.py` | the mean used is the sites' published aggregate |
| `robust/rob_*.csv`, `summary/summary_rob_*` | `code/run_robust.py` (modes noise, taskboot, tasksub, tasksub_common), `summarize_robust.py`, `feasible_counts.py` | intervals under evaluation noise, task resampling, number of tasks |
| `robust/survival_*.csv` | `code/run_survival.py` | does an optimised raise stay a win under noise (policy not re-optimised) |
| `summary/summary_capboot_*.csv` | `code/capboot.py` | bootstrap of the empirical cap (540 pairs) and its effect on feasibility |
| `summary/frontier_*.csv`, `paired_*.csv`, `summary_*_groups.csv` | `frontier.py`, `paired.py`, `summarize.py` | feasibility frontier, same-target rule ratios, stratum medians with bootstrap CIs |
| `summary/summary_variants.csv`, `variants/*` | `summarize_variants.py`, `run_core.py`, `run_weights.py`, `run_zcost.py` | slice, scale, margin, weights, cost-scale robustness |
| `uniform_baseline_*.csv` | `code/uniform_baseline.py` | capped uniform raise vs the optimal raise |
| `audit_ordinal_fix.csv` | `code/audit_ordinal.py` | rows of ordinal rules changed by the strict-model fix |
| tests | `code/tests/` | each solver equals brute force / independent LP; policies equal the solver costs |
`code/patch_rule_rows.py` replaces the rows of one rule in a run file by a rerun of that rule alone (draws and targets do not depend on
the rule list), used after the plurality solver change.

## Forbidden-material record (whole organization)
The task forbids searching for or reading the published paper on this question or anything citing or discussing it.
- `experiment-repo` (analysis): nothing of that kind was searched for or encountered; only the pinned datasets above and their cards/URLs were accessed.
- `idea-repo`: "none known" (wiki page `Encounters`, 2026-11-08; it lists the literature searches it ran; no result list contained the forbidden paper).
- `figtab-repo`: "no forbidden material encountered; no web or literature search was made" (statement posted in `experiment-repo`#11).
- `paper-repo`: "did not search for, retrieve or encounter the published paper or anything citing/discussing/mirroring it; read in full two allowed starter items (arXiv 2603.08371, 2202.03799)" (statement posted in `experiment-repo`#11; record in `paper-repo` README.md).
- `story-repo`, `idea-review-repo`, `venue-repo`, `internal-review-repo`, `external-review-repo`: not reported to this position.
