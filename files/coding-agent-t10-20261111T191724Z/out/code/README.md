# How much room is left below PPI++? — code, paper, and reproduction notes

Paper: `paper/main.pdf` (NeurIPS 2026 template, `paper/neurips_2026.sty` from the official `Formatting_Instructions_For_NeurIPS_2026.zip`;
LaTeX sources `paper/main.tex`, `paper/sec_*.tex`, `paper/app_*.tex`, `paper/checklist.tex`, `paper/refs.bib`).
Build: `cd paper && latexmk -pdf main.tex`. Main text ends on page 9 (references start there); appendices and the checklist follow.

**Disclosure.** The whole study (literature search, derivations, code, experiments, writing) was carried out by an autonomous AI research agent
(Anthropic Claude) without human intervention.

## Environment
* Python 3.11.2; virtualenv `venv/`; `numpy 2.4.6, scipy 1.17.1, pandas 3.1.1, scikit-learn 1.9.1, matplotlib 3.11.2, ppi-python 0.2.3, gdown 6.5.1, statsmodels 0.15.0` (`pip install numpy scipy pandas matplotlib scikit-learn ppi-python==0.2.3`; pymupdf was used only to preview PDF pages).
* CPU only. The container exposes 4 effective cores (cgroup quota 400000/100000) on a shared host (load averages 15–85 during runs).
* LaTeX: TeX Live (pdflatex, latexmk, bibtex).

## Data (all public; nothing is redistributed in the deliverable except through the download step)
`ppi-python==0.2.3` example data (9 `.npz` files, ~48 MB), downloaded from Google Drive by `ppi_py.datasets.load_dataset` (needs `gdown` on `PATH`, hence `export PATH=venv/bin:$PATH`);
files land in `data/`. No separate license statement exists for the `.npz` files (code is MIT). Used: galaxies, forest, alphafold, gene_expression, census_income,
census_healthcare, census_education (full (Y, Yhat) pairs, treated as populations), plankton (binary predictions; 2013 labeled / 2014 unlabeled), ballots (application).
Synthetic data are generated in `code/dgps.py`. No other data were used.

## Reproducing everything
`cd code && ./run_all.sh` (≈2.5 h wall-clock on 4 cores, ≈10 CPU-hours). Individual steps:

| step | command | time | output |
|---|---|---|---|
| download data | see `run_all.sh` | <1 min | `data/*.npz` |
| population bounds | `python -I theory.py` | ~1 min | `results/theory_pop.csv, theory_E1.csv, theory_E2.csv` |
| E3a synthetic quadratic, vary N (2000 reps) | `python -I run_experiments.py E3a --reps 2000 --procs 4` | ~25 min | `results/E3a.csv.gz` |
| E3b synthetic quadratic, vary n | `... E3b --reps 2000` | ~25 min | `results/E3b.csv.gz` |
| E3c / E3d logit-scale classifier (τ=2 / τ=4) | `... E3c / E3d --reps 2000` | ~10 min each | `results/E3c.csv.gz, E3d.csv.gz` |
| E4 plankton: binary predictor, shift | `... E4 --reps 2000` | ~10 min | `results/E4.csv.gz` |
| E2 distorted predictors (1000 reps) | `... E2 --reps 1000` | ~15 min | `results/E2.csv.gz` |
| E1b real data, vary N | `... E1b --reps 1000` | ~20 min | `results/E1b.csv.gz` |
| E1a real data, vary n | `... E1a --reps 1000` | ~25 min | `results/E1a.csv.gz` |
| ballots application | `python -I application.py` | seconds | `results/E5_ballots.csv` |
| side-information check | `python -I xgain.py` | ~30 s | `results/xgain.csv` |
| summaries | `python -I summarize.py E1a E1b E2 E3a E3b E3c E3d E4` | ~1 min | `results/summary_*.csv` |
| tables / figures | `python -I make_tables.py; python -I make_figures.py` | <1 min | `paper/tables/*.tex`, `figs/*.pdf` |

All scripts use absolute paths under `/work` (`D='/work/data/'`, `R='/work/results/'`); edit these constants if you relocate the project.
Seeds: replicate `r` of cell `c` uses `np.random.SeedSequence([20261111, crc32(c), r])` (`run_experiments.py`); the same draws are shared by all methods in a cell.
Do not name a script `numbers.py` (shadows the standard library; this happened once and was renamed to `paper_numbers.py`).

## Which script produces which table / figure
| paper item | source |
|---|---|
| Fig. 1 (theory vs empirical) | E3a → `make_figures.py:fig_theory` |
| Fig. 2 (small n, coverage) | E3b → `fig_smalln` |
| Table 1 (real data, shipped predictors) | E1a + `theory.py` → `make_tables.py:tab_real` |
| Table 2 (distorted predictors) | E2 + `theory.py` → `tab_distort` |
| Table 3 (plankton: binary / shift) | E4 → `tab_shift` |
| Table 4 (validity summary) | all of E1a, E1b, E2, E3a–d, E4 (no-shift) → `tab_validity` |
| App. Table (logit) | E3c, E3d → `tab_logit` |
| App. Table (ballots) | `application.py` → `tab_ballots` |
| App. Table (side information) | `xgain.py` → `tab_xgain` |
| App. Tables (n and N sweeps), App. figures | E1a, E1b, E2 → `tab_app_real`, `tab_app_N`, `fig_real`, `fig_distort` |
Numbers quoted in the text were read off these outputs (`results/summary_*.csv`, `code/paper_numbers.py`).

## Code layout
`code/cppi.py` (estimators: cross-fitted recalibrated PPI with lin/iso/bin10/spl/auto learners, PPI++ unclipped, classical), `code/dgps.py`,
`code/run_experiments.py` (Monte-Carlo runner), `code/summarize.py`, `code/theory.py`, `code/make_tables.py`, `code/make_figures.py`,
`code/application.py`, `code/xgain.py`, `code/pop_stats.py` (in-sample population statistics, early exploration; not used in the paper's tables), `code/run_all.sh`.

## Honest notes
* Baselines `PPI (λ=1)`, `PPI++ (ppi_py, clipped)` and the classical interval are called from `ppi-python` 0.2.3 (`ppi_mean_ci`, `classical_mean_ci`); `PPI++ (unclipped)` is our implementation (`cppi.ppi_pp_unclipped_ci`); it is the reference for width ratios. My implementation of PPI with fixed λ was checked to agree with `ppi_mean_ci(lam=...)` to 7 digits on one draw.
* Real-data cells resample i.i.d. with replacement from the finite example populations; Forest (1596 records) is affected for n ≳ 1000 (see paper).
* Replicates: 2000 (synthetic) / 1000 (real); coverage MC s.e. ≈ 0.5–0.7 points.
* Failed/abandoned work: a first launch of the experiment chain (sklearn `SplineTransformer` spline learner) was killed after ~25 min because of speed and restarted with the faster natural cubic spline in `cppi.py`; its partial output was discarded. A first E3d launch crashed on a module-name clash (see above) and was re-run. A 40-replicate smoke test of E3c was overwritten by the full run. No experiments were dropped for their results. Not done: interval-level experiments with side-information-augmented calibration; targets other than the mean; any shift-robust method.
* Population-level checks (`theory.py`, `xgain.py`) use cross-validated nonparametric fits, so the "bound" columns are estimates.

## Literature-access log (rule: do not access the earlier published study of this exact question)
* Searches run (titles only, via the provided search tool): semi-supervised mean inference (Zhang–Brown–Cai; Zhang–Bradic; Song–Lin–Zhou), POP-Inf (Miao et al.), model-calibration estimators in survey sampling,
  Robins–Rotnitzky–Zhao, classifier calibration (Niculescu-Mizil & Caruana; Guo et al.), and "Cross-prediction-powered inference Zrnic Candès".
* Encounter: the last query's result list also contained a 2025 arXiv paper titled "No Free Lunch: Non-Asymptotic Analysis of Prediction-Powered Inference" (arXiv:2505.20178) and
  "Prediction-Powered Inference with Imputed Covariates and Nonuniform Sampling" (arXiv:2501.18577). I read only the titles and the first ~3 sentences of the search-result snippets (about PPI++ vs classical intervals),
  did not open either paper, and did not use or cite them. I cannot tell whether either is the paper the task excludes; if so, nothing from it entered this work beyond that title/snippet text.
* All cited works in `paper/refs.bib` were located via search results or are the starter-list papers; page/volume details for a few classical references (e.g. Robins et al. 1994; Zhang et al. 2019) are from memory of the standard citation and were not re-verified against the publishers.
