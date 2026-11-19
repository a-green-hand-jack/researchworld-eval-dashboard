# Reproduction guide

Study: single-run reliability of SHAP attributions (Kernel SHAP, permutation SHAP) on tabular models. Design in brief: four models
(LR, XGBoost, random forest, MLP) on four datasets; 50 instances per dataset (25 random, 25 near the decision boundary); 20 explainer
runs per instance at 0.25x, 1x, 4x (and 16x on German Credit) the library default budget; each run is compared with an exact Shapley
target (closed form, interventional TreeSHAP or full enumeration) and with the other runs; noise from background redraws and model refits is
probed separately (N4). Every number in the paper's tables and figures comes from `results/tidy/*.csv`, written by `code/analyze.py` from the
raw runs in `results/<dataset>/`; see the exhibit table below for how each paper exhibit is made.

## Environment
- Python 3.11, packages pinned in `code/requirements.txt` (shap 0.51.0, xgboost-cpu 3.2.0, scikit-learn 1.9.1, folktables 0.0.12, openml 0.15.1).
  LightGBM is not used (`libgomp` missing in the sandbox). `pip install --no-cache-dir -r code/requirements.txt` (use a `TMPDIR` on a large disk).
- CPU only; every job is single-threaded (`n_jobs=1`), 2-CPU container on a shared host.

## Data (`python code/fetch_data.py`)
| dataset | source | version / retrieval |
|---|---|---|
| German Credit (d=20) | UCI 144 (`statlog+german+credit+data.zip`, `german.data`) | page updated 2023-08-10 |
| ACSEmployment, ACSIncome (d=16, 10) | folktables 0.0.12 `ACSDataSource(survey_year=2018, horizon=1-Year, survey=person)`, state CA, 40,000 rows subsampled with `RandomState(0)` | Census PUMS download, fetched when the script was run (2026-11-02) |
| Pima Indians Diabetes (d=8) | OpenML id 37 version 1 | deterministic-regime control |
Raw data are cached in `data/` (not committed; `data/raw/*.pkl`, `data/acs/`).

## Design constants (all in `code/`)
Split: stratified 70/30, `random_state=0`. Models (seed 0): LR (C=1), XGBoost (depth 4, 200 trees, lr 0.1, subsample 0.8),
RF (100 trees, depth<=8, min leaf 3), MLP (64,64; alpha 1e-2). Value function: log-odds (LR, XGB, MLP), probability (RF).
Background: 50 training rows (seed 1000). Instances: 50 per dataset (25 random + 25 near the decision boundary), shared by all models.
Budget: nsamples in {0.25, 1, 4, 16} x (2d+2048), budget in model evaluations = nsamples x 50. Explainer seeds 10000+r, r<R=20.

## Commands
```
python code/fetch_data.py
python code/run_main.py --ds german --models lr        # also xgb rf mlp; --tiers 1 2 3 (see run_main.py docstring)
python code/run_main.py --ds acs_employment --models lr  # likewise; controls: --ds acs_income, --ds pima
python code/run_n4.py --ds acs_employment --factor background   # N4: background redraw; --factor refit for refits
python code/analyze.py                                    # tidy tables in results/tidy/
```

Full order used for the delivered numbers (all resumable; finished files are skipped; every job single-threaded):
```
python code/run_main.py --ds <german|acs_employment|acs_income|pima> --models <lr|xgb|rf|mlp> --tiers 1          # Tier 1 (all four datasets)
python code/run_main.py --ds <german|acs_employment> --models <m> --tiers 2 3                                    # permutation SHAP 1x/4x and 16x (20 instances)
python code/run_main.py --ds acs_employment --models <lr|rf|mlp> --tiers 2                                       # ACSEmployment: 16x cut (see below)
python code/run_enum.py --ds german --model mlp --n 20                                                           # German MLP exact target by enumeration (2^20 coalitions)
python code/run_n4.py --ds <german|acs_employment> --factor background ; ... --factor refit                      # N4 (L=10 levels, S=3 seeds, 20 instances, 1x kernel)
python code/run_valfn.py --ds acs_employment --models lr xgb mlp                                                 # value-function sensitivity (probability)
python code/analyze.py                                                                                           # all tidy tables
```

## Cells and what was not run
Kernel SHAP `kernel_q|kernel_1|kernel_4` (0.25/1/4 x the library default nsamples = 2d+2048, `l1_reg=False`), `kernel_1_l1default`
(shap 0.51 default `l1_reg='num_features(10)'`), `perm_1|perm_4` (PermutationExplainer at the same nsamples), `kernel_16` (20 instances).
Not run, with reasons, in `results/tidy/cells_not_run.csv`: `kernel_16` on ACSEmployment (cut for throughput; 16x kept on
German); permutation SHAP and 16x on the controls ACSIncome/Pima (not planned: deterministic regime). The background-size axis, the high-dimensional
Arrhythmia probe and further datasets are not run. ACSEmployment 16x cell files that were started and stopped were deleted.

## Seeds
Split `random_state=0`; model seed 0 (N4 refit: seeds 1..10); background rows from `RandomState(1000+bg_seed)` (N4 background: bg_seed 1..10);
explainer run `r` uses `np.random.seed(10000+r)` (Kernel) / `seed=10000+r` (Permutation); N4 explainer seeds `20000+100*level+s`;
bootstrap seed 2024, 1000 draws (nested: instances, then runs within instance).

## Exact targets (validity checks)
LR: closed form on the one-hot groups (== full enumeration to 2e-16 on Pima, ACSIncome); XGBoost: interventional TreeSHAP in raw margin (== enumeration to ~1e-6);
RF: interventional TreeSHAP in probability (== enumeration to <= 2e-4, float32); ACSEmployment (d=16): full enumeration for all models and all 50 instances;
German MLP: full enumeration on the first 20 (interleaved random/near-boundary) instances only, so its error-to-target rows use n_instances=20.
Enumeration satisfies efficiency to 1e-15 (asserted in `code/run_enum.py`). `models.csv` gives the value function: log-odds for LR/XGB/MLP, probability for RF.

## Runtimes (measured wall-clock, shared host)
The host was oversubscribed during the runs (load average about 50 on 40 CPUs), so the seconds below are inflated relative to an idle CPU and
are not a benchmark. Total compute accounted by the job system: about 26 CPU-hours (Tier 1 about 9; the rest Tier 2/3, enumerations, N4,
value-function sensitivity, analysis runs). Mean seconds per explanation (one instance, one run), `results/tidy/budget_levels.csv`:

| dataset | kernel_1 | kernel_16 | kernel_1_l1default | kernel_4 | kernel_q | perm_1 | perm_4 |
|---|---|---|---|---|---|---|---|
| acs_employment | 0.41 | nan | 0.38 | 1.58 | 0.14 | 0.86 | 3.88 |
| acs_employment_probfn | 0.67 | nan | nan | nan | nan | nan | nan |
| acs_income | 0.38 | nan | 0.37 | 0.34 | 0.24 | nan | nan |
| german | 0.59 | 5.27 | 0.41 | 1.66 | 0.16 | 0.66 | 2.92 |
| pima | 0.04 | nan | 0.04 | 0.04 | 0.08 | nan | nan |

Microseconds per model evaluation by dataset and model:

| dataset | lr | mlp | rf | xgb |
|---|---|---|---|---|
| acs_employment | 5.9 | 7.6 | 6.1 | 3.4 |
| acs_employment_probfn | 7.6 | 4.6 | nan | 7.2 |
| acs_income | 7.6 | 5.3 | 2.6 | 1.7 |
| german | 5.2 | 5.6 | 6.1 | 3.6 |
| pima | 0.2 | 0.5 | 2.5 | 0.8 |

## Models (`results/tidy/models.csv`)
| index | dataset | model | value_function | test_auc | test_acc |
|---|---|---|---|---|---|
| 0 | acs_employment | lr | log-odds | 0.874 | 0.797 |
| 1 | acs_employment | xgb | log-odds | 0.905 | 0.824 |
| 2 | acs_employment | rf | probability | 0.9 | 0.814 |
| 3 | acs_employment | mlp | log-odds | 0.9 | 0.815 |
| 4 | acs_employment_probfn | lr | probability | 0.874 | 0.797 |
| 5 | acs_employment_probfn | xgb | probability | 0.905 | 0.824 |
| 6 | acs_employment_probfn | mlp | probability | 0.9 | 0.815 |
| 7 | acs_income | lr | log-odds | 0.893 | 0.814 |
| 8 | acs_income | xgb | log-odds | 0.9 | 0.819 |
| 9 | acs_income | rf | probability | 0.889 | 0.81 |
| 10 | acs_income | mlp | log-odds | 0.899 | 0.817 |
| 11 | german | lr | log-odds | 0.805 | 0.76 |
| 12 | german | xgb | log-odds | 0.785 | 0.76 |
| 13 | german | rf | probability | 0.81 | 0.757 |
| 14 | german | mlp | log-odds | 0.765 | 0.76 |
| 15 | pima | lr | log-odds | 0.871 | 0.775 |
| 16 | pima | xgb | log-odds | 0.821 | 0.753 |
| 17 | pima | rf | probability | 0.848 | 0.771 |
| 18 | pima | mlp | log-odds | 0.83 | 0.749 |

## Which script makes which result
| output | made by |
|---|---|
| `results/<ds>/raw/`, `targets/`, `instances.json`, `models.json` | `code/run_main.py`, `code/run_enum.py` |
| `results/<ds>/n4/*.npz` (phi [N, L, S, d]) | `code/run_n4.py` |
| `results/acs_employment_probfn/` (pseudo-dataset: probability value function) | `code/run_valfn.py` |
| `results/tidy/*.csv` (schema: `results/SCHEMA.md`) | `code/analyze.py` |
| `valfn_sensitivity.csv` | `code/analyze.py` (joins `acs_employment` and `acs_employment_probfn`, cell `kernel_1`) |

## Exhibits of the paper (paper numbering)
Run from the repository root: `sh figures/build_all.sh results/tidy` regenerates every figure and table; `python3 -I paper/make_numbers.py` writes
`paper/numbers.tex` (every in-text number, from `results/tidy/*.csv`); `sh paper/build.sh` builds `paper.pdf` (needs a LaTeX installation).

| paper exhibit | file | script | tidy input |
|---|---|---|---|
| Fig. 1 budget curves | `figures/fig1_budget_curves.pdf` | `figures/fig1_budget_curves.py` | `summary_ci.csv` |
| Fig. 2 gap to noise (N3) | `figures/fig3_gap_to_noise.pdf` | `figures/fig3_gap_to_noise.py` | `gap_to_noise.csv` |
| Fig. 3 noise sources (N4) | `figures/fig4_variance_components.pdf` | `figures/fig4_variance_components.py` | `variance_components_summary.csv` |
| Fig. 4 per-instance Jaccard (appendix) | `figures/fig2_instance_distribution.pdf` | `figures/fig2_instance_distribution.py` | `runs_metrics.csv` |
| Fig. 5 controls (appendix) | `figures/fig1b_budget_curves_controls.pdf` | `figures/fig1_budget_curves.py` | `summary_ci.csv` |
| Table 1 verdict counts | `tables/tab6a_claims_summary.tex` | `tables/tab6_claims.py` | `verdicts.csv` |
| Table 2 models | `tables/tab5_models.tex` | `tables/tab5_models.py` | `models.csv` |
| Table 3 per-cell verdicts | `tables/tab6_claims.tex` | `tables/tab6_claims.py` | `verdicts.csv`, `budget_levels.csv` |
| Table 4 cells not run | `tables/tab6b_cells_not_run.tex` | `tables/tab6_claims.py` | `cells_not_run.csv` |
| Table 5 verdict sensitivity | `tables/tab11_verdict_sensitivity.tex` | `tables/tab11_verdict_sensitivity.py` | `verdicts.csv` |
| Table 6 stricter notions | `tables/tab12_stricter.tex` | `tables/tab12_stricter.py` | `summary_ci.csv` |
| Tables 7-8 strata and tails | `tables/tab13_strata.tex`, `tab13b_tail.tex` | `tables/tab13_strata.py` | `runs_metrics.csv` |
| Table 9 equal budget | `tables/tab8_equal_budget.tex` | `tables/tab8_equal_budget.py` | `equal_budget.csv` |
| Table 10 planned contrasts | `tables/tab9_contrasts.tex` | `tables/tab9_contrasts.py` | `contrasts.csv` |
| Table 11 N4 ratios | `tables/tab10_n4_ratios.tex` | `tables/tab10_n4_ratios.py` | `variance_components_summary.csv` |
| Table 12 value function | `tables/tab7_valfn.tex` | `tables/tab7_valfn.py` | `valfn_sensitivity.csv` |

## Licences
Code in `code/`, `figures/` and `tables/`: MIT licence (`code/LICENSE`). Data: German Credit (UCI) is CC BY 4.0; ACS PUMS (via folktables 0.0.12, MIT code)
is released by the US Census Bureau under its terms of use (no identification of persons); Pima diabetes (OpenML id 37) has the licence "Public".
Libraries: shap 0.51.0 (MIT), scikit-learn (BSD-3-Clause), XGBoost (Apache-2.0). Data files are not redistributed here; `code/fetch_data.py` downloads them.

## Forbidden-content statement
The published paper on this question, and anything citing or discussing it, was not searched for and not encountered by the report writer, who looked only for
the method papers and background literature cited in the paper (SHAP estimators, background-set effects, explanation disagreement, stability measures, ACS data).
Statement for the code and results: to be confirmed or amended by their author (experiment-repo) when this file is reviewed.

## Caveats that affect interpretation
- RF is explained in probability, the others in log-odds; do not pool across them (value-function sensitivity in `valfn_sensitivity.csv`).
- The N4 refit probe for LR is uninformative by construction (refits with different seeds give the same model); LR explainer noise is at machine precision
  (additive model), so the variance ratio is NaN there (`explainer_at_machine_eps`).
- The shap 0.51 default `l1_reg` zeroes 10 attributions when d>10 at any budget (checked at nsamples=2088, d=20): that arm differs from the Shapley vector by construction.
- Raw data under `data/` are not committed; `code/fetch_data.py` re-downloads them (folktables fetches the Census PUMS file at run time).
