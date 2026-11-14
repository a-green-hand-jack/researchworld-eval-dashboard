# Reproduction notes (analysis part)

Status: matches analysis delivery 2 (merged in `paper-repo`#10) plus the figure/table/PDF step. One run in `code/run_all.sh` is
**not delivered**: `ollb_top500` Copeland (`results/runs/copeland_ollb_top500.csv`, appendix slice; 500 targets, exact MILP, started a second
time after a restore and not finished at the time of writing). No delivered table or figure uses it; `results/variants/var_ollb_top500.csv`
holds the other six rules on that slice. Every number in a delivered CSV was produced by the shipped code from the pinned inputs below.

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

## Commands and runtimes
Per-step wall-clock times are taken from the run logs in `logs/` of `experiment-repo` (the log named in each row of the table below); there
is no separate isolated benchmark, so treat every time, and the 8-10 h total, as approximate.
`code/run_all.sh` runs everything in order (data -> tests/theory check -> core grid -> uncertainty -> variants -> tables -> figures/PDF).
Blocks 2-5 are independent given block 1 and can be run in parallel (we ran 5-10 jobs at once on a shared host, so the figures below are
wall-clock from our run logs under that load, not isolated timings). Run sequentially on one 2-CPU container the whole script takes
roughly **8-10 hours** (the measured wall-clock times below sum to about 7.5 h plus the variants, tests and tables); it is **not** a
"few CPU hours". Run fully in parallel (about 8 CPUs) it is bounded by the longest single run, the OLLB top-500 ordinal slice (7464 s), plus the table/figure steps: about 2.5 h.

| step (`run_all.sh` block) | measured wall-clock (log) |
|---|---|
| 1 data downloads, checksums, matrices | minutes (network bound) |
| 2 tests (`pytest code/tests`) / theory check | about 2 min / under 1 min |
| 3 OLLB closed-form grid, caps emp99/emp95 (`ollb_primary_closed.log`) | 138 s |
| 3 OLLB closed-form cap sweep (`ollb_capsweep_closed.log`) | 773 s |
| 3 OLLB ordinal rules, top-50 targets, emp99+ceil (`ollb_primary_ordinal_top50.log`) | 1491 s |
| 3 HELM primary caps, 10 rules (`helm_primary.log`) | 518 s |
| 3 HELM cap sweep, 9 rules x 5 caps incl. Copeland (`helm_capsweep.log`) | 3445 s |
| 3 HELM Copeland, emp99T + ceil (`copeland.log`) | 983 s |
| 3 OLLB top-500 Copeland, emp99 (**undelivered**) | not finished; more than 1 h CPU so far |
| 4 OLLB noise / task bootstrap, closed forms, 300 draws (`rob_ollb_*_closed_*.log`) | 78 s / 44 s |
| 4 OLLB noise / task bootstrap, ordinal rules, 60 draws (`rob_ollb_*_ord_*.log`) | 3720 s / 3841 s |
| 4 HELM noise (200 draws) / task bootstrap (200) / task subsets (60) | 3290 s / 1169 s / 189 s |
| 5 OLLB `nomerge`, `top500` (six rules, emp99+ceil), `raw` slices (`var_ollb.log`, `var_ollb_raw.log`) | the `top500` ordinal rules took 7464 s; the other slice runs under 2 min each |
| 5 margin (eps 1, 2), weights, sigma-unit costs | 10-30 min each (see `margin.log`, `weights.log`, `zcost.log`) |
| 6 `code/make_tables.sh` | about 10 min |
| 7 `code/build_figures.sh` (figures, tables, PDF) | about 2 min |

Step 7 was re-run from the delivered `results/`: every PNG, JSON sidecar and `.tex` table regenerated byte-identically; PDFs differ only in
embedded timestamps.

## Figures and tables -> commands
Run from the delivery root (`paper-repo`); `R=results`. `code/build_figures.sh` runs all of these and then `cd paper && latexmk -pdf main.tex`.
The same map, with inputs, claims and per-file SHA-256 sidecars, is `figures/MANIFEST.md` (figtab position).

| paper item | command | input (under `results/`) |
|---|---|---|
| F1 `F_ollb_primary`, F2 `F_helm_primary` | `python3 figures/src/fig_rank_rules.py R {ollb,helm} figures/F_{ollb,helm}_primary --caps primary` | `core_{ollb,helm}.csv` |
| oracle versions (appendix) | same with `--caps ceil` and `figures/F_{ollb,helm}_oracle` | `core_*.csv` |
| F3 `F_{ollb,helm}_capgrid` | `python3 figures/src/fig_cap_grid.py R {ollb,helm} figures/F_{ollb,helm}_capgrid` | `core_*.csv` |
| F4 `F_helm_scaling` | `python3 figures/src/fig_scaling.py R figures/F_helm_scaling` | `summary/summary_rob_helm_tasksub_emp99T.csv` |
| F5 `F_robust` | `python3 figures/src/fig_robust.py R figures/F_robust` | `summary/summary_rob_*`, `core_*.csv` |
| T2 theory check, T3 rules x ranks, T4 frontier | `python3 figures/src/tables.py R tables` | `theory_check.csv`, `core_*.csv`, `summary/frontier_*.csv` |
| T5 HELM cap sweep frontier, T6 variants | `python3 figures/src/tables_ext.py R tables` | `summary/frontier_helm.csv`, `summary/summary_variants.csv` |
| PDF | `cd paper && latexmk -pdf main.tex` | `paper/main.tex`, `tables/*.tex`, `figures/*.pdf` |

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
| tests | `code/tests/` | each solver equals brute force / an independent LP on small random instances |

## Forbidden-material record
The task forbids searching for or reading the published paper on this question or anything citing or discussing it. During this
work (the whole `experiment-repo` position, which is the analysis position: data, solvers, experiments, result tables) nothing of that
kind was searched for or encountered. Only the pinned datasets above and their cards/URLs were accessed. This record covers that
position only; the other positions attest for their own parts.
