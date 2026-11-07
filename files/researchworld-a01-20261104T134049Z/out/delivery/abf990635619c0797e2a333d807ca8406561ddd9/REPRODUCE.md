# Reproduction notes (analysis part)

Status of this file: final. Every number in a delivered CSV, table and figure was produced by the shipped code from the pinned
inputs below. One optional run was started and **stopped without a result**: exact Copeland on the OLLB top-500 slice (500 MILPs of
about 500 models each; stopped after about 2.2 h with no output file, because the paper does not use it). It is not in `code/run_all.sh`;
the command is `python3 code/run_core.py ollb_top500 emp99 copeland all OUT.csv`. Copeland is reported for HELM only.

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

## Commands and run time
`code/run_all.sh` runs everything in order (data -> tests/theory check -> core grid -> uncertainty -> variants -> tables); the tables
step alone is `bash code/make_tables.sh`. Run times below were measured from the job logs on the shared 2-CPU container while up to
eight of these jobs ran at once, so a run alone on a free machine is faster. Steps marked (est.) were not timed individually.

| step | time |
|---|---|
| data download and processing, tests, theory check | about 10 min (est.), 5 min, < 1 min |
| OLLB closed-form grid (`emp99`, `emp95`; then `ceil`, `front0`, `gain5/10/20`) | 2.5 min; 13 min |
| OLLB ordinal top-50 (`emp99`, `ceil`) | 25 min |
| HELM primary caps, all rules | 9 min |
| HELM cap sweep (10 rules x 5 caps, Copeland included) | 57 min |
| Copeland on HELM (`emp99T`, `ceil`) | 16 min |
| OLLB noise and task bootstrap, closed forms (300 draws) | 1.3 and 0.7 min |
| HELM task bootstrap (200 draws) / HELM evaluation noise (200 draws) | 20 min / 55 min |
| HELM task-subset scaling (60 draws) | 10 min (est.) |
| OLLB ordinal noise / task bootstrap (60 draws each) | about 73 min each |
| OLLB variants (`nomerge`, `top500` with ordinal rules, `raw`) | 92 min |
| margin 1/2 points, Dirichlet weights, sigma-unit costs | 30 min in total (est.) |
| `code/make_tables.sh` | 10 min (est.) |

Summed over the rows this is about 8.4 h of job time (503 min, including the estimated rows). That is what one sequential run of
`code/run_all.sh` costs on this container under the same load; "roughly ten hours" in an earlier draft of the paper was a rounded-up
version of this sum, and the paper should say "about nine hours of summed job time" (or give 8.4 h). The steps after the data block
read only `data/processed` and are independent of each other (`make_tables.sh` needs all of them), so they can run as parallel jobs;
the wall-clock time is then bounded below by the longest step (92 min). We ran them in parallel but did not time the whole pipeline
end to end, so we give no total wall-clock figure.

## Script -> table / figure
**Numbers as in the paper** (Figure/Table n of `paper/main.tex`; plan ids T2-T6, F1-F5 in brackets). Commands run from the repository
root with `R=results`; `figures/MANIFEST.md` has the full argument lists and input hashes. Generators of the figures and tables are in
`figures/src/` (presentation); each reads only the result files named here, which come from the analysis scripts in the last column.

| paper item | generator command | result files read | analysis scripts that produce them |
|---|---|---|---|
| Figure 1 (F1, F2) | `python3 figures/src/fig_rank_rules.py $R ollb figures/F_ollb_primary --caps primary` and `... helm figures/F_helm_primary --caps primary` | `core_{ollb,helm}.csv` | `run_core.py`, `assemble_core.py` |
| Table 1 (T4) | `python3 figures/src/tables.py $R tables` | `core_*.csv`, `summary/frontier_*.csv` | `run_core.py`, `assemble_core.py`, `frontier.py` |
| Table 2 (T3) | same | `core_*.csv` | `run_core.py`, `assemble_core.py` |
| Figure 2 (F4) | `python3 figures/src/fig_scaling.py $R figures/F_helm_scaling` | `summary/summary_rob_helm_tasksub_emp99T.csv` | `run_robust.py tasksub`, `summarize_robust.py` |
| Figure 3 (F5) | `python3 figures/src/fig_robust.py $R figures/F_robust` | `summary/summary_rob_*` (OLLB closed forms and ordinal, HELM noise and task bootstrap), `core_*.csv` | `run_robust.py noise/taskboot`, `summarize_robust.py` |
| Table 3 (T2) | `python3 figures/src/tables.py $R tables` | `theory_check.csv` | `theory_check.py`, `mti/theory.py` |
| Figure 4 (oracle cap) | `fig_rank_rules.py $R ollb figures/F_ollb_oracle --caps ceil` and `... helm figures/F_helm_oracle --caps ceil` | `core_*.csv` | `run_core.py`, `assemble_core.py` |
| Figure 5 (F3, OLLB) | `python3 figures/src/fig_cap_grid.py $R ollb figures/F_ollb_capgrid` | `core_ollb.csv` | `run_core.py`, `assemble_core.py` |
| Figure 6 (F3, HELM) | `python3 figures/src/fig_cap_grid.py $R helm figures/F_helm_capgrid` | `core_helm.csv` | `run_core.py`, `assemble_core.py` |
| Table 4 (T5) | `python3 figures/src/tables.py $R tables` | `summary/summary_variants.csv` | `run_core.py`, `run_weights.py`, `run_zcost.py`, `summarize_variants.py` |
| Table 5 (T6) | same | `summary/paired_*.csv` | `paired.py` |

If the paper's float order changes, `paper/main.tex` is the authority for the numbers; the file names in the second column do not change.

**Other outputs**

| output | script | claim it supports |
|---|---|---|
| `results/core_{ollb,helm}.csv` | `code/run_core.py` (+ `code/assemble_core.py`, from `results/runs/`) | minimum investment (K, L1, Linf) to be strictly first by cap x rule x target |
| `results/official_rules_check.csv` | `code/official_rules_check.py` | the mean we use is the sites' published aggregate |
| `results/summary/summary_*_groups.csv` | `code/summarize.py` | medians by rank stratum with bootstrap CIs |
| `results/variants/*`, `results/robust/*` | `run_core.py`, `run_weights.py`, `run_zcost.py`, `run_robust.py` | raw runs of the variants and Monte-Carlo robustness checks |
| tests | `code/tests/` | each solver equals brute force / an independent LP on small random instances |

## Forbidden-material record
The task forbids searching for or reading the published paper on this question or anything citing or discussing it. During this
work (analysis position): nothing of that kind was searched for or encountered. Only the pinned datasets above and their cards/URLs
were accessed.
