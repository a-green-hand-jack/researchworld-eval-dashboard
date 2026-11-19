# Code, data steps and result tables of the study (`code/`)

This directory is the code delivery of the analysis role. It contains everything needed to re-run the analyses and to regenerate the files the
figures and tables read, except the raw per-fold records (≈ 380 MB) and the data of the five LLM score matrices (licences unstated, so not
redistributed; rebuilt from the pinned public sources by `src/build_*.py`, see `data/SOURCES.md`).

| Path | Content |
|---|---|
| `src/` | method code: factor-analysis EM with missing data (`fa.py`), selectors incl. greedy A/D-optimal, complement-error greedy, k-medoids, forward regression (`bselect.py`), inference methods (`infer.py`), cross-validation protocol and metrics (`protocol.py`), closed-form forecasts and bounds (`theory.py`), settings (`settings.py`, `mteb_matrix.py`), analysis helpers (`analysis.py`: paired and family-clustered bootstrap, Holm), data builders (`build_*.py`, `data_mteb.py`, `fetch_olmb_results.py`) |
| `exp/` | one script per experiment (E0–E8, H3, H3c, E7), the analysis scripts (`analyze_*.py`), `export_figtab.py` (writes `figdata/`), `make_pm.py`, `deliver.sh` (builds this directory) |
| `tests/` | closed-form checks against direct Gaussian conditioning and brute force: `python3 -I tests/test_closed_forms.py` (≈ 1 min) |
| `figdata/` | the result files the figures and tables are drawn from (schema: `figdata/README.md`) |
| `results/<matrix>/` | `curves.csv` (error versus k with CIs), `primary.csv` (pre-declared comparisons, Holm), `fa_rank.csv`, `info_rep*.json` (rank scores, eigenvalues, fit times), `per_model.parquet` (mean over repetitions per held-out model × k × selector × method: the table the bootstrap runs on) |
| `results/{E1,E2,E6,E8,H3,H3r,FAM}/` | summary tables of the synthetic, leakage/groups/cost, shift/stopping, history-size/missingness, nonlinear-imputer and family-aware experiments |
| `data/` | `mteb_long.parquet`, `mteb_models.parquet` (MTEB results repository, CC0-1.0, pinned commit in `data/SOURCES.md`/below), `SOURCES.md` (URLs, commits, licences, caveats, build commands for the LLM matrices) |
| `PRIMARY_COMPARISONS.md` | the comparisons and the Holm family declared before the confirmatory runs |
| `requirements.txt` | versions of the libraries used |

Run every command from this directory (`code/`). Quick checks that need only it:
```
python3 -I tests/test_closed_forms.py                               # closed forms
python3 -I exp/analyze_main.py A2                                   # curves.csv, primary.csv from per_model.parquet (reproduces results/A2/*.csv up to float32 rounding)
python3 -I exp/analyze_fam.py A1 A2 B                               # family-aware CIs and the forward-regression / k-medoids comparisons (results/FAM/*)
```
Scripts that read the raw records (`export_figtab.py` for forecasts and coverage, `analyze_h1.py`, `analyze_e6.py`, `analyze_e2.py`, `e_floor.py`) need the
`results/<M>/rec_rep*.parquet` files, which are produced by the commands below (A2 ≈ 35 min, A1 ≈ 75 min, B ≈ 2.5 h per repetition, LLM matrices
minutes to ≈ 3 h; table at the end).

