# Reproduction notes (analysis part)

Status of this file: first delivery. Items marked **pending** are still running and are listed in `code/run_all.sh`; every number
in a delivered CSV was produced by the shipped code from the pinned inputs below.

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

## Commands
`code/run_all.sh` runs everything in order (data -> tests/theory check -> core grid -> uncertainty -> variants -> tables). Approximate
wall-clock on the shared 2-CPU container (several jobs ran at once, so these are upper-ish figures): data minutes; tests about 2 min;
theory check < 1 min; OLLB closed-form grid ~15 min; OLLB ordinal top-50 ~25 min; HELM primary caps, all rules ~10 min; HELM cap sweep
(10 rules x 5 caps, Copeland included) ~1 h; Copeland on HELM at `emp99T` and `ceil` ~20 min; OLLB noise / task bootstrap (closed forms,
300 draws) ~1 min each; HELM task bootstrap (200 draws, all rules) ~16 min; HELM evaluation noise ~1 h; OLLB ordinal noise / task
bootstrap (60 draws) ~1 h each; OLLB variants (`nomerge`, `top500` ordinal rules, `raw`) 1-2 h; margin, weights, sigma-unit costs
10-30 min each; `code/make_tables.sh` (core assembly, summaries, frontier, paired comparisons) ~10 min.

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
work (analysis position): nothing of that kind was searched for or encountered. Only the pinned datasets above and their cards/URLs
were accessed.
