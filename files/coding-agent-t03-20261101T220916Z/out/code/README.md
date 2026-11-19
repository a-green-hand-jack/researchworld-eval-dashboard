# Single-run reliability of SHAP on tabular models — code and reproduction guide

Paper: `paper/main.tex` (NeurIPS 2026 template, `paper/main.pdf`). All numbers/tables/figures in the paper are produced by the
scripts in `code/` from data downloaded by `code/get_data.py`; nothing is hand-entered except the prose that quotes them.

## Environment
* Python 3.11.2 (venv), Linux. Versions: see `requirements.txt` (numpy 2.4.6, scipy 1.17.1, pandas 3.1.0, scikit-learn 1.9.1,
  shap 0.51.0, xgboost 3.2.0, numba 0.68.1, folktables 0.0.12, openml 0.15.1, pyarrow 26.0.0, matplotlib 3.11.2).
* `python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt`
* LaTeX: TeX Live 2022 (`latexmk -pdf main.tex` in `paper/`); template `neurips_2026.sty` from the official
  `Formatting_Instructions_For_NeurIPS_2026.zip` (downloaded from media.neurips.cc, unmodified).
* The machine reports 40 cores but its cgroup quota is 4 CPUs (`/sys/fs/cgroup/cpu.max` = 400000 100000); all `--procs 4`
  settings and run times below refer to this quota. RAM use < 10 GB (German tables use ~0.4 GB/process).

## Data (downloaded 2026-11-01/02 by `code/get_data.py`)
| data | source | version |
|---|---|---|
| German Credit | UCI id 144 (`statlog+german+credit+data.zip`), CC BY 4.0 | 1,000 x 20, bad credit = 1 |
| Pima Diabetes | OpenML data id 37, version 1 (upload 2014-04-06) | 768 x 8 |
| Give Me Some Credit | OpenML id 46929, version 1 (upload 2025-04-30) | 150,000 rows; we use a seeded 40,000-row subsample |
| ACSIncome, ACSEmployment | folktables 0.0.12 -> Census ACS PUMS 2018 1-Year person file, California (378,817 rows) | seeded 40,000-row subsample |
| Arrhythmia (stress test only) | UCI id 5, CC BY 4.0 | 452 x 279 (262 non-constant), label = non-normal |

## Seeds
Instance sampling `RandomState(123)`; background rows `Xtr.sample(random_state=1)`; train/test split seed 0 (replicate: 1,
via `SHAP_SPLIT=1`); model seed 0; dataset subsampling seed 0; per-run seeds `SeedSequence([dataset, model, instance, m, estimator, run])`
(`exp_main.seed_of`). All experiments are deterministic given these seeds (numba RNG is seeded inside the sampler).

## Pipeline and run times (4-core quota)
`code/run_all.sh` runs everything in order. Individual steps (wall-clock):

| step | command (in `code/`) | time | output |
|---|---|---|---|
| data | `python get_data.py` | 1 min | `data/raw` |
| main experiment | `python exp_main.py --ds pima,gmsc,acsincome,acsemployment,german --procs 4` | 75 min | `results/main/<ds>_<model>/inst_*.pkl` |
| background experiment | `python exp_bg.py --procs 4` | 5 min | `results/bg` |
| background pairs | `python exp_bgpair.py --procs 4` | ~8 min | `results/bgpair` |
| retraining baseline | `python exp_retrain.py --procs 4` | 6 min | `results/retrain` |
| shap library validation | `python exp_shaplib.py --procs 4` | 10 min | `results/shaplib` |
| high-dim stress test | `python exp_highd.py --procs 4` | 27 min | `results/highd` |
| replicate (seed 1) | `SHAP_SPLIT=1 SHAP_OUT=/work/results/main_rep1 python exp_main.py --ds pima,gmsc,acsincome --procs 4` | ~17 min | `results/main_rep1` |
| aggregation | `python analyze_main.py 4` (replicate: `SHAP_SRC=... SHAP_DST=... python analyze_main.py 4`) | 1 min | `results/summary*/` |
| figures/tables | `python gen_setup.py; python analyze_figs.py; python analyze_rep.py` | 2 min | `paper/figs`, `paper/gen` |

Total CPU time of the final pipeline is about 10 CPU-hours (+ about 3 CPU-hours of aborted/exploratory runs, see below).

## Which script makes which table/figure
| paper item | script (function) | inputs |
|---|---|---|
| Table 1 (setup) | `gen_setup.py` | `results/main` |
| Fig. 1 `fig_reliability_budget`, Table 5 `tab_reliability` | `analyze_figs.py` (`fig1`, `table_reliability`) | `results/summary/inst_level.parquet` |
| Fig. 2 `fig_mechanism`, App. Fig. `fig_sd` | `analyze_figs.py` (`fig2`, `fig_sd`) | `inst_level.parquet` |
| Table 2 `tab_est` | `analyze_figs.py` (`est_table`) | `inst_level.parquet` |
| Fig. 3 `fig_certificate`, Table 3 `tab_cert` | `analyze_figs.py` (`cert`) | `run_level.parquet`, `tworun.parquet` |
| Fig. 4 `fig_standards`, Table 6 `tab_standards` | `analyze_figs.py` (`standards`) | `results/retrain`, `results/bgpair`, `inst_level.parquet` |
| Fig. 5 `fig_background` | `analyze_figs.py` (`bg_fig`) | `results/bg` |
| Table 4 `tab_highd`, App. Table 7 `tab_shaplib` | `analyze_figs.py` (`highd_and_lib`) | `results/highd`, `results/shaplib` |
| App. Table 8 `tab_rep` | `analyze_rep.py` | `results/summary`, `results/summary_rep1` |
| numbers quoted in prose (pooled CIs, budget quantiles, near-tie shares, SE/SD, Spearman, replicate near-tie shares, ...) | `extra_stats.py` -> `paper/gen/extra_stats.json` (canonical); `paper/gen/numbers.json`, `paper/gen/*.csv` from `analyze_figs.py` | `results/*` |

## Code map
* `estimators.py` — exact Shapley from a value table; numba sampler porting the sampling logic of `shap.KernelExplainer`;
  leverage-score variant (our re-implementation of the idea of Musco & Witter 2024); antithetic permutation sampling; sandwich SE.
* `common.py` — datasets, preprocessing (players = original features; one-hot columns grouped), models, value-table builder.
* `metrics.py` — relative L2, top-k, Jaccard, Spearman, RBO, Nogueira stability, pairwise agreement.
* `test_est.py` — unbiasedness / SE-calibration check on random games (`python test_est.py 10`).
* `exp_*.py`, `analyze_*.py`, `gen_setup.py`, `run_all.sh` — as above.

## Deviations, aborted runs and caveats (honest log)
* A first launch of the main experiment with 40 worker processes on the 4-CPU quota was aborted after ~28 min (German RF tables
  too slow: ~11 CPU-min per instance for all four models); the German experiment was then reduced to 24 instances and 50-tree
  RFs (also applied to Pima since the rule is `n_train < 1000`) and everything was re-run from scratch. A first launch of the
  retraining experiment included ACSEmployment (d=16) and was aborted as too expensive; it was restricted to d <= 10.
* Budget m=32 was run but is excluded from all analyses (under-determined regression for d >= 16); m >= 64 is analysed.
* MLP regularisation for small datasets (alpha=1, 50 epochs, no early stopping) was chosen after seeing that early stopping on
  10% validation gave AUC 0.65–0.70 on German/Pima (5 splits of those datasets were used, which are the same data later explained;
  it does not use any attribution results).
* The Kernel SHAP sampler is a port, not the library itself; the validation (`exp_shaplib.py`) compares both.
* `results/` holds raw results (~0.35 GB); `data/raw` the downloaded data.

## Content-restriction log
The task forbids reading the paper that already studied this question. I did not search for it by title/author/results.
Literature searches performed: "Improving KernelSHAP ...", "Sampling permutations for Shapley value estimation" and
"stability of SHAP explanations random sampling variability repeated runs" (the last one returned only unrelated items
such as an LIME-stability paper, a thesis on explanation stability under training objectives, and application papers; I read
titles/snippets only and opened none). I also fetched the arXiv abstract pages of the starter-list papers 2, 3, 4, 5, 6 and
of Covert & Lee 2021 and Mitchell et al. 2021 to verify their metadata. No page that discusses or reproduces the forbidden paper
was knowingly accessed.

## Note on bootstrap intervals
All percentile bootstrap intervals use seeded `numpy` generators, but different scripts consume different random streams, so interval end-points from `extra_stats.py` and `analyze_figs.py` can differ by up to ~0.5 points in the last digit(s); the paper quotes `extra_stats.py` for pooled headline intervals.
