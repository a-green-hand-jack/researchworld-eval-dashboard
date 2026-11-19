# experiment/

Code, raw results and derived tables of the single-run SHAP reliability study. Run everything from this directory.

- `code/`: data loaders, models, explainers (`explain.py`), the per-cell runner `run_cell.py`, queue scripts, timing script, `smoke_check.py` (small-run check, see `../REPRODUCE.md` §4).
- `analysis/`: raw arrays -> tables (`build_tables.py`, `summarize.py`, `compute_matched.py`, `diagnostic.py`, `export_long.py`, `german_checks.py`, `logit_sensitivity.py`, `retrain_notes.py`, `retrain_sensitivity.py`, `ties.py`, `seed_correlation.py`, `runtime_from_logs.py`; `run_all.sh RAW OUT` runs them all).
- `results/raw/`: raw attribution arrays per (dataset, model, stage); only completed cells are delivered.
- `results/logs/`: stage time stamps of every cell run (source of `runtime_cells.csv`).
- `results/tables/`, `results/long/`: derived tables and the long format. Layout and measure definitions: `results/README.md`.
- Environment, data, seeds, commands: `../REPRODUCE.md`.
