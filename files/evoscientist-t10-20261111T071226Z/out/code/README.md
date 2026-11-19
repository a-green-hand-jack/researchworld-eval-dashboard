# How much shorter can prediction-powered confidence intervals get? (code + paper)

Paper: `paper/main.pdf` (NeurIPS 2026 template, `paper/main.tex`, tables in `paper/tables/`, figures in `paper/figs/`).
Code: `code/`. Raw summaries of every experiment: `results/*.csv`.

## Question and answer in one paragraph
Target: population mean E[Y] with a fixed predictor f, n labels, N unlabeled points. Within all estimators
`mean(Y-h(f)) + mean_U h(f)` the optimum is h = N/(n+N) * E[Y|f]; PPI++ is optimal iff E[Y|f] is affine in f and realises a
fraction rho^2 = Corr(E[Y|f], f)^2 of the available variance reduction (Prop. 1, Cor. 1-2 in the paper).
Empirically: <=~2% headroom on the nine real `ppi-python` datasets (once the lambda-clip of `ppi_py` is removed), 7-27% on
synthetic miscalibrated/non-monotone predictors, up to 35% on real outcomes whose predictor scores are put on another monotone scale;
small-n undercoverage of plug-in Wald intervals; tuned lambda<1 loses coverage under shift.

## Environment
Python 3.11.15; `pip install -r requirements.txt` (numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, matplotlib 3.11.2,
joblib 1.6.0, ppi-python 0.2.3, gdown 6.5.1). LaTeX: TeX Live `pdflatex`+`latexmk`+`bibtex`. CPU only.
Data: `ppi-python==0.2.3` example collections (9 `.npz`, ~48 MB), downloaded by `code/download_data.py` from the package's
Google-Drive links into `data/` (not redistributed here; no separate licence statement for the `.npz` files; code is MIT).
Template: official NeurIPS 2026 files (`paper/neurips_2026.sty`, checklist from `paper/tpl/checklist.tex`), downloaded from
`https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip`.

## Reproduction (run from the repository root; set `OMP_NUM_THREADS=1` etc. to avoid oversubscription)
```
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
python code/download_data.py                 # ~1 min
python code/test_methods.py                  # sanity checks (own PPI/PPI++ vs ppi_py, coverage smoke test), ~1 min
python code/run_real.py 2000                 # real-data resampling, R=2000     -> results/real_summary.csv      (906 s wall)
python code/run_synth.py 2000                # synthetic, R=2000                -> results/synth_summary.csv     (1420 s wall)
python code/run_extra.py 2000                # shift, ballots deployment, covariate extension (R=500 for the latter)
                                             #   -> results/shift_summary.csv, ballots_deploy.csv, ext_x_*.csv   (948 s wall)
python code/run_distort.py 1000              # score-scale stress test, R=1000  -> results/distort_summary.csv   (396 s wall)
python code/pool_stats.py                    # pool statistics table (needs oracle caches from run_real.py)
python code/make_figs.py                     # all figures (figs/, paper/figs/) and LaTeX tables (paper/tables/)
python code/paper_numbers.py                 # prints the numbers quoted in the paper text (for checking)
python code/check_refs.py                    # verifies arXiv metadata of the cited items
cd paper && python build_checklist.py && latexmk -pdf main.tex
```
Wall times were measured on a **shared** 40-core / 250 GB machine (load average 30-280 from other users) with 28-36 worker
processes (`joblib`/loky); per-process CPU share was often only 10-70%, so CPU-hours were not measured (the brief estimated < 8 CPU-h).
Total wall time of all runs: ~1 h (memory was not measured; each worker holds one dataset pool, at most ~380k floats per array).
Seeds: base seeds 20261111 (synthetic), 20261112 (real), 20261113/20261114 (shift / covariates), 20261115 (distortion);
each configuration uses `SeedSequence([base, config_id])`, so reruns are bit-reproducible given the same library versions
(joblib scheduling does not affect results).

## Which script produces which table/figure of the paper
| Item | Source |
|---|---|
| Synthetic width figure and table | `run_synth.py` -> `make_figs.py` (`fig_synth_width.pdf`, `tab_synth.tex`) |
| Real-data width table and figure | `run_real.py` -> `make_figs.py` (`tab_real_width.tex`, `fig_real_width.pdf`) |
| Coverage figure and table | `run_real.py`, `run_synth.py` -> `make_figs.py` (`fig_coverage.pdf`, `tab_coverage.tex`) |
| Score-scale stress test table | `run_distort.py` -> `make_figs.py` (`tab_distort.tex`) |
| Sensitivity-to-k table | `make_figs.py` (`tab_sens.tex`) from real/synth CSVs |
| Shift . no-shift control table | `run_extra.py` -> `tab_shift.tex` |
| Pool statistics table | `pool_stats.py` -> `tab_pool.tex` |
| Covariate extension table | `run_extra.py` -> `tab_ext_x.tex` |
| Ballots deployment table | `run_extra.py` -> `tab_ballots.tex` |
| Theory vs empirical figure | `make_figs.py` (`fig_theory_vs_emp.pdf`) |
Table/figure numbers in the PDF are assigned by LaTeX in order of appearance; use the file names (`\input` . `\includegraphics` in `paper/main.tex`).

## Files
- `code/methods.py`: all interval estimators (classical, PPI, PPI++ via `ppi_py` and unclipped own, post-stratified PPI,
  natural-spline controls, cross-fitted isotonic and boosting controls, t-corrected variants).
- `code/common.py`: replication loop, summaries (coverage with Wilson CI, paired width ratios), asymptotic variances (theory).
- `code/synth_lib.py`, `code/real_lib.py`: data-generating processes / resampling, oracle quantities.

## Deviations, history and honest notes
- Target restricted to the population mean (stated in the paper). No other estimands were run.
- Real-data experiments resample i.i.d. with replacement from each pool (pool mean = truth); N = 10^4 even for the small pools
  (forest, ballots), so unlabeled repeats occur there. Plankton/ballots use only their stored labeled parts for coverage;
  the real ballots split (1027 labeled, 78150 unlabeled) is used only for the deployment example (no ground truth).
- Real-data "bound" columns use E[Var(Y|f)] from 10-fold cross-fitted gradient boosting on the pool (cached in `data/oracle_*.npy`).
- Smoke tests with R=20/40 were run during development; their outputs were overwritten and are not used anywhere.
- **A first full real-data run (R=2000) used a post-stratified PPI baseline whose standard error ignored the random stratum
  shares; it undercovered badly for large n (e.g. 0.73 on gene expression at n=2000).** The baseline was fixed
  (`strat_ppi` in `code/methods.py`), t-corrected variants were added, and *all* reported results come from the re-run with the fixed code.
  The first run's numbers appear nowhere in the paper. A first attempt of the synthetic run was aborted (unpicklable closures) and rerun.
- The `ppi_py` PPI++ baseline clips lambda to [0,1] (read in the package source); the paper therefore also reports an unclipped
  own implementation and attributes differences between the two to the clip (Cor. 2). Our own PPI (lambda=1) matches the package
  (checked in `test_methods.py`).
- Hyperparameters (k=4 knots, 5 folds, K=5 strata) were fixed before the real-data results; k in {3,6} are reported as sensitivity.
- The efficiency-bound statement beyond within-class optimality is argued, not proved (paper, App. A).
- Not completed / not done: no estimands other than the mean; no bootstrap or exact small-sample intervals; no real data with an
  independent unlabeled sample with ground truth other than plankton (shift experiment).
- Literature: only the starter list and the `ppi-python` source were used; the arXiv API was queried for the metadata of the cited items
  (`code/check_refs.py`); full texts were not read.
- **Forbidden-content statement:** no searches were made for the study mentioned in `deliverable.md`; the only network accesses were
  Google Drive (ppi-python data), the NeurIPS template/call-for-papers pages, PyPI (pip), and the arXiv API for the listed references.
  Nothing matching the forbidden category was encountered or read.
