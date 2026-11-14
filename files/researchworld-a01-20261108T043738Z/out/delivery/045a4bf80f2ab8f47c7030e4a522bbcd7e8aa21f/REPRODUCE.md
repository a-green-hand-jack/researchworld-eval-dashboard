# Reproduction notes (analysis part)

Status of this file: final analysis delivery. Every run in `code/run_all.sh` has finished and every number in a delivered CSV was
produced by the shipped code from the pinned inputs below; nothing is pending. `code/run_all.sh` ends with the figure and table
commands (block 7), which live in `figures/src/` of the delivery root.

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
`code/run_all.sh` runs everything in order (data -> tests/theory check -> core grid -> uncertainty -> variants -> tables -> figures and paper tables). Approximate
wall-clock on the shared 2-CPU container (several jobs ran at once, so these are upper-ish figures): data minutes; tests about 2 min;
theory check < 1 min; OLLB closed-form grid ~15 min; OLLB ordinal top-50 ~25 min; HELM primary caps, all rules ~10 min; HELM cap sweep
(10 rules x 5 caps, Copeland included) ~1 h; Copeland on HELM at `emp99T` and `ceil` ~20 min; OLLB noise / task bootstrap (closed forms,
300 draws) ~1 min each; HELM task bootstrap (200 draws, all rules) ~16 min; HELM evaluation noise ~1 h; OLLB ordinal noise / task
bootstrap (60 draws) ~1 h each; OLLB variants (`nomerge`, `top500` ordinal rules, `raw`) 1-2 h; margin, weights, sigma-unit costs
10-30 min each; `code/make_tables.sh` (core assembly, summaries, frontier, paired comparisons) ~10 min.

## Target sets and the "first" convention
"First" means **strictly first by at least eps = 1e-3** (`--eps` in `code/run_core.py`): the target's rule value must exceed the best
other model's value by eps. A model that is first only through an exact tie is therefore a *target*, not `already_first`, and its
minimum investment is the tie-break cost (L1 = eps = 0.001 for score rules). `status = already_first` (cost 0) is set only for the
unique strict leader. Consequences, checked on `results/core_*.csv` (all caps):

| dataset, rule | target rows | `already_first` rows | why |
|---|---|---|---|
| HELM, every rule except median | 78 | 1 (Claude 3.5 Sonnet 20241022) | unique strict leader |
| HELM, median | 79 | 0 | Claude 3.5 Sonnet (20241022) and DeepSeek v3 have the identical median (89.8148); both have rank_rule 1 and cost 0.001 (= eps). This is the tie convention, not a bug. The mean-rule leader is not strictly first under the median. |
| OLLB, score rules (mean, median, min, geomean, harmonic, pow-2) | 4496 targets minus the leader | 1 | unique strict leader |
| OLLB, ordinal rules (50 best targets only) | 50 | Borda 1; Condorcet 0; plurality 0 | Condorcet: no Condorcet winner exists on OLLB, so the best model is also a target (rank_rule is NaN); plurality: two models tie for the most first places (rank_rule 1 for both; cost of the leader = the extra margin needed to break the tie, 0.16 pts on emp99) |

For statistics by initial rank under a rule, the tied leaders sit in the rank-1 stratum with cost ~eps; they are tie-break
artefacts and should be read as "0 up to tie-breaking". The paper's target-set sentence should say that the set of targets is every
model that is not the *unique strict* leader under the rule at hand (so 79 under HELM median, 78 otherwise).

## Paper table / figure -> command
Numbers are those of the paper (`paper/main.tex`, order of appearance); file names are figtab-repo's (`figures/MANIFEST.md` has the
inputs, SHA-256 sidecars and the claim each supports). Run from the delivery root after `code/run_all.sh` has filled `results/`;
`R=results`. The paper itself is built with `cd paper && latexmk -pdf main.tex`.

| paper item | file | command | analysis inputs |
|---|---|---|---|
| Fig. 1 (main result, OLLB and HELM, primary caps) | `figures/F_ollb_primary`, `F_helm_primary` | `python3 figures/src/fig_rank_rules.py $R {ollb,helm} figures/F_{ollb,helm}_primary --caps primary` | `core_{ollb,helm}.csv` |
| Table 1 (feasibility frontier) | `tables/T4_frontier_{ollb,helm}.tex` | `python3 figures/src/tables.py $R tables` | `core_{ollb,helm}.csv` (agrees with `summary/frontier_*.csv`, which adds bootstrap CIs; not wired in) |
| Table 2 (rules by rank stratum, primary caps) | `tables/T3_rules_ollb_emp99.tex`, `T3_rules_helm_emp99T.tex` | same | `core_*.csv` |
| Fig. 2 (scaling with number of tasks, HELM) | `figures/F_helm_scaling` | `python3 figures/src/fig_scaling.py $R figures/F_helm_scaling` | `summary/summary_rob_helm_tasksub_emp99T.csv` |
| Fig. 3 (noise and task-bootstrap stability) | `figures/F_robust` | `python3 figures/src/fig_robust.py $R figures/F_robust` | `summary/summary_rob_*`, `core_*.csv` |
| Table 3 (appendix, closed forms vs solvers) | `tables/T2_theory_check.tex` | `python3 figures/src/tables.py $R tables` | `theory_check.csv` |
| Fig. 4 (appendix, oracle cap) | `figures/F_ollb_oracle`, `F_helm_oracle` | `python3 figures/src/fig_rank_rules.py $R {ollb,helm} figures/F_{ollb,helm}_oracle --caps ceil` | `core_*.csv` (cap `ceil`) |
| Figs. 5 (OLLB) and 6 (HELM) (appendix, cap grid) | `figures/F_ollb_capgrid`, `F_helm_capgrid` | `python3 figures/src/fig_cap_grid.py $R {ollb,helm} figures/F_{ollb,helm}_capgrid` | `core_*.csv` (all caps) |
| Table 4 (appendix, paired comparison with the mean rule) | `tables/T5_paired_*.tex` (`T5K_*` for K) | `python3 figures/src/tables.py $R tables` | `summary/paired_*.csv` |
| Table 5 (appendix, variants) | `tables/T6_variants_{compact,ollb,helm}.tex` | same | `summary/summary_variants.csv` |
| other `tables/T3_*`, `figures/*` not in the main numbering | | same commands | see `figures/MANIFEST.md` |

## Script -> results file
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
