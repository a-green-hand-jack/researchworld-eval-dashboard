# Code and results: subset-based prediction of full-benchmark scores

Own implementation (the `benchpred` package of the data repository was inspected, not used). All numbers in `results/` are produced by the scripts below from the pinned data.

## Environment
Python 3.11.2, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, torch 2.14.1+cpu, pyarrow 26.0.0, joblib 1.6.0. CPU only. Run every script with single-threaded BLAS (`OMP_NUM_THREADS=1 ...`; the scripts export it) — with default threading the sweeps were >10x slower on a shared host.

## Data
`scripts/fetch_data.sh` downloads the 13 score matrices + model lists from `socialfoundations/benchmark-prediction` at the pinned commit `55faff496947789f94e6b5908c77cbc3e84f81ad` into `/hutian/data/raw` (override with `DATA=` / `BP_DATA=`). Preprocessing (`src/data.py`, `src/protocol.py`): models with accuracy ~0 dropped; exact duplicate model rows (identical response vectors) removed (`--no_dedup` runs keep them). No missing entries exist (`results/data_audit.csv`).

## Pipeline (script → output)
| step | command | output | approx. cost (2 CPUs, shared host) |
|---|---|---|---|
| main grid | `scripts/run_main.sh "<benchmarks>"` | `results/raw/main` (10 baseline methods) | ~1.5 h (mmlu_pro dominates) |
| designs/ablations | `scripts/run_m2.sh` | `results/raw/m2` | ~15 h wall on a loaded host (mmlu_pro) |
| proposed + refs | `scripts/run_m4.sh` | `results/raw/m4` (`mass_ens`, `sources_only`, ridge-AIPW, MASS ablations) | ~15 h wall (mmlu_pro) |
| sensitivity | `scripts/run_ablate.sh "<benchmarks>" [family]` | `results/raw/ablate` | ~3 h |
| sources-only baseline choice | `scripts/run_source_cv.sh`, `src/best_baseline.py results` | `results/source_cv/`, `results/best_baseline.csv` | <1 h |
| tables | `scripts/make_tables.sh "<benchmarks>"` then `python3 -I src/merge_tables.py results results/raw/main results/raw/m2 results/raw/m4 results/raw/ablate` | `results/*.csv`, `provenance.json` | ~0.5 h |

Raw per-target predictions (`results/raw/*/*.parquet`, 53 MB) are attached to the release `raw-predictions` of `world/experiment-repo` rather than committed.

## Seeds
Item-selection seed of repetition `rep` at budget `n`: `10000*rep + n`. `random` protocol: model split seed `1000+rep`; `family`: `2000+rep`; reduced source sets: `777+rep`; latent-model fit seed 0 (fixed); bootstrap: seed from benchmark/protocol/n. Source-CV: inner reps `100..104`.

## Protocols (src/protocol.py)
`random`: 20% random models as targets (new draw per rep). `extrap`: top 20% by full score are targets (single split). `extrap_f01/f03`: 10%/30%. `*_s025/_s05`: 25%/50% of source models kept. `*_nodedup`: duplicates kept. `family`: whole organisations (prefix before `/`, OLL only) held out until >=20% of models. Budgets n in {10,20,50,100,200} (sensitivity: all five).

## Uncertainty
95% percentile bootstrap, B=200 (`src/make_tables.py`). Resampling unit: target models for `extrap*` (metric averaged over item-selection seeds); repetitions (= independent model split + item seed) for `random`, `family`, `random_s*`. Paired differences use identical resamples. Cross-benchmark summaries (`aggregate.csv`): benchmark is the unit; geometric-mean ratio (RMSE/MAE, `effect_def=geomean_ratio`) or mean difference (rank metrics, `mean_diff`) with 2000-resample benchmark bootstrap and a Wilcoxon signed-rank p (only for >= 6 benchmarks). The `subset` column gives the benchmark set: `all13`, `non_dev9` (all but the four development benchmarks ifeval, arc_challenge, gpqa, gsm, on which the `mass_ens` predictor was chosen), `dev4`, `oll` (7), `helm` (6), `narrow3` (gpqa, musr, openllm_math: narrow spread of model accuracies, `data_audit.csv`). Wilcoxon p is NOT an independent-test p-value: HELM benchmarks share models, `dev4` chose the `mass_ens` predictor, and subsets with few benchmarks have very wide bootstrap CIs.

## Result files (`results/`)
`cells.csv` (bench, protocol, method, n, metric, mean, ci_lo, ci_hi, n_models, n_reps, n_src; metrics mae, rmse, spearman, kendall, bias=pred-true, rmse_over_sd), `paired.csv` (method vs ref, delta_mean + CI; refs: random, ridge, aipw_rand, anchor_irt, the strongest-by-source-CV baseline of that benchmark, and `mass_ens` vs every method including `sources_only` and `mass`; `cells.csv` and `paired.csv` carry a boolean `dev_bench`), `aggregate.csv` (refs random, ridge, `best_cv`; all methods, so `mass` and `mass_ens` are co-headline), `ranking_by_subset.csv` (absolute mean Spearman/Kendall per method, subset, protocol, n, with min/max over benchmarks), `proposed_ci_counts.csv` (per subset, for `mass_ens` and `mass`, number of benchmarks whose paired CI excludes 0 in favour/against, refs incl. `best_cv`), `ess_gain.csv`, `coverage.csv` (MASS-Ens interval), `predictions_headline.csv` (n=50,100; seed-averaged for `extrap*`), `splits.csv`, `data_audit.csv`, `best_baseline.csv`, `source_cv/`, `provenance.json`.

## Provenance / disclosure
- While inspecting the data repository (required by data.md) I read its README, which summarises the conclusions of its paper (arXiv:2506.07673, a starter-literature item). Nothing else of that paper was read.
- Development choices (the predictor of `mass_ens`) were made after a pilot that looked at target-model errors on four benchmarks; see the paper's limitations.
- Not implemented: Pacchiardi assessor (needs item text), Active Evaluation Acquisition (trained policy), metabench GAM. `anchor_irt`, `anchor_aipw`, `irt_info` are simplified, own-named variants.
