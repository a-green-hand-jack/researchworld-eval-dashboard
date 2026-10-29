# Predicting full-benchmark LLM scores from few items — code and paper

Layout
- `paper/` — LaTeX source (`main.tex`, `sec_*.tex`, `refs.bib`, NeurIPS 2026 style file `neurips_2026.sty`), generated `tables/` and `figs/`, compiled `main.pdf`.
- `code/` — all code (`data.py`, `irt.py`, `bp.py`, `run_exp.py`, `analyze.py`, `stats_util.py`, `load_results.py`, `make_data_table.py`), `requirements.txt`, and `dev/` (development scripts used to fix hyper-parameters; see below).
- `data/raw/` — downloaded data (not re-distributable beyond its MIT licence; re-downloadable with the commands below); `data/SHA256SUMS.txt`.
- `results/raw/<tag>/` — one pickle per (benchmark, split type, seed) job; `logs/` — run logs.

## Environment
Python 3.11.2, `python3 -m venv venv && venv/bin/pip install -r code/requirements.txt` (numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.1, pandas 3.1.0, joblib 1.6.0, matplotlib 3.11.2; `pypdf` only for checking page counts). LaTeX: `latexmk -pdf` with TeX Live (pdflatex, natbib).
The sandbox reports 40 cores but has a 4-core CPU quota (cgroup `cpu.max`); all timings below are for 4 cores.

## Data (version used)
Repository https://github.com/socialfoundations/benchmark-prediction at commit `55faff496947789f94e6b5908c77cbc3e84f81ad` (MIT). Files `data/scores/{arc_challenge,bbh,gpqa,ifeval,mmlu_pro,musr,openllm_math,commonsense,gsm,legalbench,math,med_qa,mmlu}.jbl`, `*_models.jbl` for the Open LLM Leaderboard benchmarks and the two model-list text files:
```
mkdir -p data/raw && cd data/raw
B=https://raw.githubusercontent.com/socialfoundations/benchmark-prediction/55faff496947789f94e6b5908c77cbc3e84f81ad
for f in arc_challenge bbh gpqa ifeval mmlu_pro musr openllm_math commonsense gsm legalbench math med_qa mmlu; do curl -sSfL -O $B/data/scores/$f.jbl; done
for f in arc_challenge bbh gpqa ifeval mmlu_pro musr openllm_math; do curl -sSfL -O $B/data/scores/${f}_models.jbl; done
```
(SHA-256 of what we used: `data/SHA256SUMS.txt`.) The `benchpred` package of that repository was **not** used; all methods are implemented in `code/`.

## Run (from `code/`)
```
venv/bin/python -I code/data.py                       # data summary -> results/data_summary.txt  (seconds)
venv/bin/python -I code/run_exp.py --tag main --seeds 0-29 --budgets 10,25,50,100,200 --auto --jobs 4     # main grid, 990 jobs, ~3.5 h on 4 cores
venv/bin/python -I code/run_exp.py --tag shift --protocols top10,top50,bottom --seeds 0-9 --budgets 25,100 --designs rand,strat,pps1.0,anchor --jobs 3   # shift severity, ~1.5 h
venv/bin/python -I code/analyze.py main paper         # all main/appendix tables + figures from results/raw/main (~10 min)
for K in 20 50 100; do venv/bin/python -I code/run_exp.py --tag src$K --benchmarks arc_challenge,gpqa,ifeval,musr,openllm_math,mmlu,gsm --protocols random,top --seeds 0-9 --budgets 25,100 --designs strat,pps1.0 --max_sources $K --jobs 1; done   # source-size ablation, ~10 min each
venv/bin/python -I code/analyze.py shift paper        # shift-severity table
venv/bin/python -I code/analyze_src.py paper          # source-size tables
venv/bin/python -I code/make_data_table.py            # paper/tables/data.tex
cd paper && latexmk -pdf main.tex
```
Seeds: split seed `s` -> `default_rng(10000+s)`; coreset/IRT-initialisation -> `default_rng(s)`; AUTO inner splits -> `default_rng(777000+s)`. Development runs used seeds >= 1000 (tags `dev`, `dev2`) and 2000-2007 (`code/dev/t_*.py`) and are not in any reported table.

## Which script makes which table/figure
| item in paper | file(s) | script |
|---|---|---|
| Table 1 (main relative RMSE) | `paper/tables/main_rel_rmse.tex` | `analyze.py main` |
| Fig. 1 (curves) | `paper/figs/curves.pdf` | `analyze.py main` |
| Table 2 (bias) | `tables/bias_n100.tex` | `analyze.py main` |
| App. Table data / abs. RMSE | `tables/data.tex`, `tables/abs_rmse_n100.tex` | `make_data_table.py`, `analyze.py main` |
| App. full budgets, Spearman, Kendall, pairs, design effects, wins, ablations, AUTO choice | `tables/{full_rel_rmse,spearman,kendall,pairs,design_effects,wins,ablation_*,auto_choice}.tex` | `analyze.py main` |
| App. per-benchmark figures | `figs/perbench_*.pdf` | `analyze.py main` |
| App. source-set size | `tables/src_size_n{25,100}.tex` | `analyze_src.py` |
| App. shift severity | `tables/shift_rel.tex`, `tables/shift_bias_n100.tex` | `analyze.py shift` |

## Method code map
- `bp.py`: designs (`d_rand`, `d_strat`, `d_pps` = VA-PPS, `d_anchor`, `d_dopt`), estimators (`e_mean`, `e_lin`, `e_ridge`, `e_irt_family` = IRT / plug-in / AIPW / Cal-IRT / Cal+AIPW / ShrinkCal / cross-fitted AIPW), `auto_select` (pseudo-shift tuning), `evaluate_split` (one source/target split).
- `irt.py`: multidimensional 2PL fit (L-BFGS), batched MAP ability, Platt recalibration.
- `run_exp.py`: split protocols (`random`, `org`, `top`, `top10`, `top50`, `bottom`) and the parallel job runner.
- `stats_util.py`: relative RMSE and hierarchical bootstrap.

## Development scripts (`code/dev/`)
Used only to choose fixed hyper-parameters (IRT regularisation, prior variance, Platt penalty, shrinkage constant) on seeds >= 1000/2000: `t_irt.py` (IRT sanity), `t_var.py` (prior variance, regularisation, recalibration), `t_lam.py` (Platt penalties), `t_shr.py` (pretest shrinkage), `t_dev*.py` (summaries of the `dev`/`dev2` runs). Their outputs were printed to the terminal and are not stored; they are not needed to reproduce the paper's tables.

## Disclosures
- Restricted-content statement: see Appendix "Reproducibility and disclosures" of the paper (we read only the data repository's README; we did not read the NeurIPS 2025 paper listed in the starter literature nor search for the restricted paper).
- The whole study was done by an autonomous AI agent (Claude Sonnet 5.5).
