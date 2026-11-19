# Repeat-run reliability of Kernel SHAP on tabular models

Layout: `code/` (scripts), `results/` (raw `.npz` per cell, `summary.csv`, `headline.json`, LaTeX table fragments, logs), `figs/`, `paper/` (`main.tex`, `main.pdf`, NeurIPS 2025 style, `refs.bib`, `checklist.tex`).

## Environment
Python 3.11, venv: `python3 -m venv venv && . venv/bin/activate && pip install shap scikit-learn xgboost folktables pandas scipy matplotlib openml` (exact versions in `requirements.txt`: shap 0.51.0, scikit-learn 1.9.1, xgboost 3.2.0, numpy 2.4.6, folktables 0.0.12, openml 0.15.1). CPU only, 16 GB RAM limit (run.py uses 16 workers, 5 for Arrhythmia; `export OMP_NUM_THREADS=1`). LaTeX: pdflatex/latexmk.

## Data (downloaded automatically by `code/common.py`)
OpenML ids 31 (German credit, credit-g), 37 (Pima), 46929 (Give Me Some Credit), 5 (Arrhythmia); folktables ACSIncome and ACSPublicCoverage, California, survey year 2018, 1-year, person (cached under `data/acs`, ~ census.gov download). Rows capped to 20,000 (seed 0); split 70/30 stratified, seed 0. Kaggle/UCI direct sources were not used.

## Run (from `code/`)
```
python run.py german pima gmsc acs acspc arr     # ~1.5 h wall-clock on 16 cores; <=16 CPU-hours (results/*.npz)
python analyze.py                                # tables (results/tex_*.tex, summary.csv, headline.json) and figs/*.pdf
python aucs.py                                   # results/auc.csv, tex_auc.tex
python check_xgb.py                              # results/check_xgb.txt (reference validation)
cd ../paper && latexmk -pdf main.tex
```
Seeds: data split 0; background rows RandomState(1); instances RandomState(1) (same stream); Kernel SHAP repeat seeds are a deterministic function of (instance, budget, run) in `run.py`; model seed 0 (retrain seeds 1-5; background resample RandomState(100+s)); bootstrap RandomState(0).
Note: the final results were produced by several invocations (german/gmsc/acs, then acspc, then xgboost for all datasets after the log-odds fix, then arr rf, then pima), as listed in `results/run*.log`; earlier invocations crashed with out-of-memory (reference budget then reduced from 32768 to 16384) and one XGBoost run (probability-space reference) was discarded; see paper Sec. 4 and App. A.

## Which script makes what
- Fig. 1 `figs/match_vs_budget.pdf`, Fig. 2 `figs/gap.pdf`, Table 1 (`results/headline.json`), Table 2 (`results/tex_noise.tex`), Tables A2-A3 (`tex_match3.tex`, `tex_relerr.tex`): `analyze.py` (from `run.py` outputs). Appendix AUC table: `aucs.py`. Sec. 4 XGBoost reference check: `check_xgb.py`.

## Notes
- NeurIPS 2026 template URL returned 404 when checked (2026-11-14); the 2025 style is used.
- No forbidden content (the paper the task excludes, or anything citing it) was searched for or encountered.
