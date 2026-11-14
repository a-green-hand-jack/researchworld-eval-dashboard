# Predicting full-benchmark LLM scores from few items: a controlled study under distribution shift

Everything in the paper (`paper/main.pdf`, LaTeX source in `paper/`) is produced by the code in `code/` from the pinned public data.
Template: ICML 2026 (`icml2026.sty`, downloaded from media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip). ICML has no separate checklist; the mandatory Impact Statement is included.

## Environment
* Python 3.11.2, packages pinned in `code/requirements.txt` (numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.1, joblib 1.6.0, pandas 3.1.0, matplotlib 3.11.2); `venv` created with `python3 -m venv venv && venv/bin/pip install -r code/requirements.txt`. LaTeX: TeX Live pdfLaTeX + bibtex.
* CPU only. The sandbox exposed 40 cores but a cgroup quota of 4 CPUs; all timings below are for 4 cores. Scripts set `OMP_NUM_THREADS=1` and parallelise over (benchmark, regime, replicate) tasks.

## Data (version)
* `https://github.com/socialfoundations/benchmark-prediction`, commit `55faff496947789f94e6b5908c77cbc3e84f81ad`, files `data/scores/*.jbl` (13 benchmarks) and `*_models.jbl` model lists (7 Open-LLM-Leaderboard benchmarks); MIT licence. Only data files were downloaded (`code/download_data.sh`); the repository's `benchpred` package was neither cloned nor used.
* The `.jbl` files are pickles (untrusted). `code/prep_data.py` loads them with a restricted unpickler (numpy/builtin types only) and writes `data/*.npz`. Duplicate model names (identical rows; 6--19 per benchmark) are dropped (first kept) in `bplib.load_bench`.

## Reproduction (run from `/work`)
`sh code/run_all.sh` runs everything. Individual steps (base seed 20261102; every task seeds `np.random.SeedSequence([seed, bench_idx, regime_idx, rep])`):

| step | command | approx. time (4 cores) |
|---|---|---|
| data | `sh code/download_data.sh /work/data_raw; python -I code/prep_data.py data_raw data` | 1 min |
| main experiment (13 benchmarks x 3 regimes x 30 splits; IID, Extrap-50, Extrap-25) | `python -I code/run_main.py --reps 30 --tag main2 --workers 4` | 80 min |
| family hold-out regime (7 Open LLM Leaderboard benchmarks x 30 splits) | `python -I code/run_main.py --reps 30 --tag main2 --workers 4 --regimes fam --benches arc_challenge,bbh,gpqa,ifeval,mmlu_pro,musr,openllm_math` | 38 min |
| unbiasedness / coverage (200 random subsets per split) | `python -I code/run_cover.py --workers 3 --reps 5` | ~20 min |
| ablations (n. source models, latent dim., prior, folds, recalibrated predictor, regression estimators) | `python -I code/run_ablate.py --workers 3 --reps 10` | ~45 min |
| analysis | `data_summary.py`, `analyze_main.py`, `analyze_extra.py`, `analyze_diag.py`, `make_paper_tables.py` | ~10 min |
| paper | `cd paper; pdflatex main; bibtex main; pdflatex main; pdflatex main` | 1 min |

## Which script produces what
* `code/bplib.py` -- data loading, IRT fit, selectors, estimators (mean, ridge, kNN, p-IRT, gp-IRT, CF, CF-EB0/EB1, recalibrated predictor, GREG), metrics. `code/analyze_lib.py` -- loading and clustered bootstrap.
* Table 1 (main, `tab:main`) <- `analyze_main.py` -> `results/summary_main.pkl` -> `make_paper_tables.py` -> `results/tables/combined_k50.tex`.
* Fig. 1 (`fig_relrmse_vs_k.pdf`), Fig. 2 (`fig_bias_by_strength.pdf`), appendix heat map (`fig_heatmap_k50.pdf`) <- `analyze_main.py`.
* Significance tests (Wilcoxon over benchmarks) <- `analyze_main.py` -> `results/significance.csv`.
* Table 2 (coverage) <- `run_cover.py` + `analyze_extra.py` -> `results/tables/cover.tex`, `results/cover_summary.csv`.
* Fig. 3 (bias mechanism) and `results/diag.csv` <- `analyze_diag.py`.
* Ablation tables <- `run_ablate.py` + `analyze_extra.py` (+ `make_ablation_tables.py`); appendix full tables <- `make_paper_tables.py`; dataset table <- `data_summary.py`.

## Version history of the main experiment (for transparency)
The main experiment was run twice. Version 1 (`results/old_main/raw_main_v1`, tag `main`) had no recalibrated predictor; after the ablation showed that a per-target recalibration changes the picture, the estimators `pirt_cal`, `cf_cal`, `eb0_cal` were added (they use a separate RNG so all subset draws are unchanged) and everything was re-run as tag `main2`, which is what the paper reports. `python -I code/check_repro.py` verifies that all estimators present in both versions are reproduced exactly (max abs difference 0.0 over 1217 tasks). The family hold-out regime was only run in version 2 (a partial run in version 1 was aborted).
The ablation (`run_ablate.py`) and coverage (`run_cover.py`) runs were done with the code state before `est_pirt_cal` was changed to take item weights (identical numerics for equal weights).

## Which script produces what (continued)
* `make_ablation_tables.py` -> `results/tables/abl_*.tex` (appendix ablation tables); `check_repro.py` -> reproducibility check above.

## Notes on honesty / scope
* All numbers in the paper are produced by the scripts above (raw per-task results are in `results/raw_*`; summary CSVs in `results/`). Replicates are 30 independent splits (10 for ablations, 5 splits x 200 subsets for coverage).
* Baselines (anchor points, tinyBenchmarks-style p-IRT/gp-IRT, ridge, kNN) are our own re-implementations following the published descriptions; they are not the authors' code and their numbers should not be read as reproductions of the original papers.
* Literature access: I consulted arXiv abstract pages of the starter-list papers (and for tinyBenchmarks the method section, to implement p-IRT/gp-IRT). For Zhang et al. (starter item 6) I read only the abstract page; I did not read its body, code or any other page about it. I did not search for, and to my knowledge did not encounter, any page of the excluded published paper or pages citing/discussing it. Note that the abstract of Zhang et al. states that they propose an AIPW-inspired estimator; this is why the paper positions the CF estimator as classical model-assisted survey estimation rather than as a new idea.
* The unfinished/negative items: a hypothesis that p-IRT bias is explained by items that no source model solves was tested and rejected (`analyze_diag.py`); CF-EB1 reduces RMSE but hurts rank correlation; a per-target recalibrated predictor and a regression estimator gave no improvement over CF/stratification (ablation).

## Layout
`paper/main.tex` (+ `paper/sections/*.tex`, `paper/refs.bib`, ICML 2026 style files) compiles to `paper/main.pdf`; it `\input`s generated tables from `results/tables/` and figures from `figs/` through relative paths (`../results/tables`, `../figs`), so keep the directory layout. Raw per-task results: `results/raw_main2` (main + family), `results/raw_cover`, `results/raw_ablate`, `results/old_main/raw_main_v1` (superseded first version, kept for `check_repro.py`).
