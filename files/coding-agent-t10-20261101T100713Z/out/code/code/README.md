# Headroom for prediction-powered confidence intervals (code and reproduction)

Paper: `../paper/main.pdf` (source `../paper/main.tex`, NeurIPS 2026 template, `neurips_2026.sty`).

## Environment
Python 3.11.2, packages in `requirements.txt` (numpy 2.4.6, scipy 1.17.1, pandas 3.1.0, scikit-learn 1.9.1,
matplotlib 3.11.2, ppi-python 0.2.3, gdown 6.5.1). CPU only. LaTeX: `latexmk -pdf main.tex` in `../paper`.

## Data (all public; version fixed)
`python download_data.py` downloads the nine `.npz` example sets of `ppi-python==0.2.3` into `../data/`
(first use of `ppi_py.datasets.load_dataset`, via gdown / Google Drive, ~48 MB). The repository states an MIT license for
the code; it gives no separate license for the `.npz` files (see their `examples/*.ipynb` for original sources).
Synthetic data are generated in `datasets.py` (designs S0-S7, Appendix B of the paper).

## Run order (wall-clock on a shared 40-core machine with ~4-5 effective cores; `--procs` = worker processes)
```
python run_experiments.py --suite real  --reps 1000 --out ../results/real.csv.gz  --procs 38   # ~42 min
python run_experiments.py --suite synth --reps 1000 --out ../results/synth.csv.gz --procs 38   # ~41 min
OMP_NUM_THREADS=2 python theory.py                      # population constants -> results/theory_pop.csv (~25 min)
python analysis.py                                      # summaries, predicted-vs-observed
python run_boot.py  --reps 500 --B 399 --out ../results/boot.csv.gz                            # ~24 min
python run_shift.py --reps 1000 --out ../results/shift.csv.gz                                  # few min
python run_noclip.py                                                                           # ~1 min
python make_report.py                                   # figures -> ../figs, LaTeX tables -> ../paper/tables
(cd tests && python check_fast.py)                           # sanity check of fast.py vs ppi_py / methods.py
```
Seeds: `numpy.random.SeedSequence([20261101, crc32(dataset), n, N, rep])` (other scripts add a tag), so every
replication is reproducible independently of the number of processes. `theory.py` uses seed 1 for subsampling/synthetic draws
(and fixed `random_state=0` for its CV folds); histogram gradient boosting is deterministic with these settings.
Run python scripts without `-I` (they import sibling modules).

## Which script produces which result
| paper item | scripts |
|---|---|
| Table 1 (main_real/main_synth), Tables 4-5 (n=1000, n=50) | `run_experiments.py` -> `analysis.py` (+`theory.py`) -> `make_report.py` |
| Fig. 1 (width ratio vs n, N) | same |
| Fig. 2 (predicted vs observed) | `theory.py`, `analysis.py` (`pred_vs_obs.csv`), `make_report.py` |
| Fig. 3, Table 2 (coverage, bootstrap-t) | `run_experiments.py` (Wald), `run_boot.py`, `make_report.py` |
| Table 3 (shift) | `run_shift.py`, `make_report.py` |
| Table 6 (clipped vs unclipped lambda) | `run_noclip.py`, `make_report.py` |
| numbers quoted in text | `results/summary_{real,synth}.csv`, `results/boot_summary.csv`, `results/auto_choice_*.csv`, `results/pred_vs_obs.csv`, `results/theory_pop.csv` |

## Files
`methods.py` (classical/PPI/PPI++ via ppi_py; cross-fitted AIPW estimators), `fast.py` (closed-form versions for bootstrap),
`datasets.py` (populations), `results/` (raw replication-level output `*.csv.gz` and summaries).

## Honest notes
* The classical and PPI baselines are ppi_py's (`ddof=0` standard errors); our estimators use `ddof=1`.
* Width ratios are ratios of mean widths with a paired bootstrap over replications (300 resamples).
* `statsmodels` is installed but unused. t-quantile coverages (`cov_t`) are stored in `summary_*.csv` but not discussed.
* Proposition 3 (validity of the cross-fitted estimator) is only sketched in the paper.
* Literature check: the starter list and three further titles (Zhang-Brown-Cai; Miao et al.; Robins-Rotnitzky-Zhao) were
  looked up by exact title in the literature-search tool to verify they exist. No searches were made for, and no
  page was knowingly encountered about, the work excluded in `deliverable.md`.
