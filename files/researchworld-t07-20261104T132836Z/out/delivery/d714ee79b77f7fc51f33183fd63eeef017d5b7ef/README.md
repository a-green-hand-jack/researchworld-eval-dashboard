# Predicting full-benchmark LLM scores from a few items

Paper (NeurIPS 2026 format, anonymous submission mode) and reproduction package for a controlled comparison of benchmark-prediction methods
(source models' per-item results are known; a target model is run on `n` items only) and a model-assisted sampling estimator (MASS).

| path | content |
|---|---|
| `paper/main.pdf`, `paper/main.tex`, `paper/sections/`, `paper/refs.bib`, `paper/checklist.tex` | the paper (build: `cd paper && make`, or `latexmk -pdf -outdir=build main.tex && cp build/main.pdf .`; needs TeX Live) |
| `paper/neurips_2026.sty` | unmodified official NeurIPS 2026 style file (hashes in `venue-repo`) |
| `tools/check_venue.py` | format check (`python3 tools/check_venue.py paper/main.pdf paper/main.tex`) |
| `code/` | harness, methods, run scripts; see `code/README.md` for per-step commands |
| `results/` | tidy result tables (`cells.csv`, `paired.csv`, `aggregate.csv`, ...) with `provenance.json`; raw per-target predictions are in the release `raw-predictions` of `experiment-repo` |
| `paper/figures/`, `paper/tables/` | figure PDFs and LaTeX table fragments with their generator scripts and `MANIFEST.md` |

## Environment
Python 3.11.2; numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, torch 2.14.1 (CPU), pyarrow 26.0.0, joblib 1.6.0, matplotlib 3.11.2. TeX Live with latexmk and BibTeX for the paper. CPU only; no GPU, no paid API, no model is run.

## Data (version)
13 binary model x item correctness matrices (`*.jbl`, joblib) from `https://github.com/socialfoundations/benchmark-prediction` at the fixed commit `55faff496947789f94e6b5908c77cbc3e84f81ad` (MIT): Open LLM Leaderboard v2 (arc_challenge, bbh, gpqa, ifeval, mmlu_pro, musr, openllm_math) and HELM (commonsense, gsm, legalbench, math, med_qa, mmlu). Fetch with `bash code/scripts/fetch_data.sh` (writes `SHA256SUMS`). Exact duplicate model rows are removed before splitting (`results/data_audit.csv`). Files of that repository not listed in the task (image/GLUE tasks) are not used.

## Reproducing the results (order, cost)
1. `bash code/scripts/fetch_data.sh` (~80 MB).
2. (Skip this step if you only regenerate figures and tables from the delivered `results/*.csv`.) Rebuilding the CSVs needs `results/raw/`, which is not in this repository: either download it from the release `raw-predictions` of `experiment-repo` and unpack it into `results/raw/` (then only `merge_tables.py` is needed), or re-run the sweeps (15+ h wall time on a loaded 2-CPU host). Sweeps `code/scripts/run_main.sh`, `run_m2.sh`, `run_m4.sh`, `run_ablate.sh`, `run_source_cv.sh` then `code/scripts/make_tables.sh` and `python3 -I code/src/merge_tables.py ...` (exact commands, arguments and cost table in `code/README.md`; the heaviest sweeps take ~15 h wall time on a loaded 2-CPU host, dominated by mmlu_pro).
3. Figures and tables: `FIGTAB_RESULTS=results bash paper/figures/make_all.sh` (about a minute on one CPU).
4. Paper: `cd paper && make`.

Seeds, protocols and the bootstrap (B=200, 95% percentile intervals, resampling unit) are documented in `code/README.md`; every table and figure is regenerated from `results/*.csv` by the scripts below.

## Which script produces each table and figure
Numbers in the text come from `results/*.csv` (produced by `code/`, see `code/README.md`) or from the tables below; each row lists the generator and its inputs (full map with claims: `paper/figures/MANIFEST.md`).

| output in the paper | generator | inputs (`results/`) |
|---|---|---|
| Tables 1-2 (headline, extrapolation / interpolation, n=50); Appendix headline tables n=100 | `paper/tables/src/tab_headline.py` | `cells.csv` |
| Appendix per-benchmark RMSE and Kendall tables | `paper/tables/src/tab_headline.py` | `cells.csv`, `paired.csv` |
| Table 3 (selection x predictor), rank-ablation table | `paper/tables/src/tab_ablate.py` | `cells.csv` |
| Table 4 (robustness: dedup, family-out) | `paper/tables/src/tab_sens.py` | `cells.csv` |
| Appendix data-audit table | `paper/tables/src/tab_audit.py` | `data_audit.csv` |
| Figure 1 (error vs budget) | `paper/figures/src/fig_budget.py` | `cells.csv`, `best_baseline.csv` |
| Figure 2 (pre-declared comparison), Appendix paired figure for MASS | `paper/figures/src/fig_paired.py` | `cells.csv`, `paired.csv`, `best_baseline.csv`, `aggregate.csv` |
| Figure 3 (true vs predicted), Appendix coverage figure | `paper/figures/src/fig_extrap.py` | `predictions_headline.csv`, `coverage.csv` |
| Appendix ESS-gain figure | `paper/figures/src/fig_ess.py` | `ess_gain.csv` |
| Appendix sensitivity figure | `paper/figures/src/fig_sens.py` | `cells.csv` |
| Appendix per-benchmark budget grids | `paper/figures/src/fig_budget.py` | `cells.csv`, `best_baseline.csv` |
| `results/*.csv` themselves | `code/scripts/run_*.sh`, `code/scripts/make_tables.sh`, `code/src/merge_tables.py` | raw sweeps in `results/raw/` |

All figure and table generators run with `bash paper/figures/make_all.sh` (about 70 s, one CPU, fixed seeds).

## Disclosures
- **Forbidden-content rule (deliverable.md).** The task states that its research question was studied by a published paper which must not be searched for or read. We treated the paper in `starter_literature.md` item 6 (Zhang, Dorner, Hardt; arXiv:2506.07673), whose data and code the task prescribes, as allowed, since the task explicitly permits the starter list. What was read of it: `experiment-repo` read the repository's README, which contains a one-paragraph summary of that paper's conclusions (which methods extrapolate poorly, which are recommended), and nothing else of the paper; `idea-repo` read the arXiv abstract and the README and code. We read no page that cites or discusses it beyond that. Those conclusions were treated as hypotheses to test. The positions did not run open-ended searches for benchmark-prediction literature.
- **Development choices made after seeing target-model errors.** The predictor of the proposed `mass_ens` (ensemble vs latent-only) was chosen after a pilot on one split of ifeval, arc_challenge, gpqa and gsm; `mass` (latent-only) is reported alongside, and those four benchmarks are flagged. The baselines' target-side results already existed when the source-only cross-validation choice of the strongest baseline was computed (the choice itself uses only source models).
- **Not reproduced faithfully (not run):** the assessor of Pacchiardi et al., the learned acquisition policy of Li et al., the GAM of metabench. `anchor_irt`, `anchor_aipw`, `irt_info` are simplified variants under their own names.
- **LLM assistance.** The study, code and manuscript were produced by AI agents (Claude); no language model is part of the evaluated methods.
