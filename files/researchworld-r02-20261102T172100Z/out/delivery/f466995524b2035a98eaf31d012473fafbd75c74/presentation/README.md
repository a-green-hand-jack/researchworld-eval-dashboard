# Reproduce the figures and tables

The delivered assets use completed analysis evidence from experiment-repo revision recorded in `presentation/artifact_manifest.json`. The pilot is excluded. Current assets cover all ten methods: seven core methods, the matched-seed known-ratio oracle, total variation and forward KL, with 100 independent datasets in each of 160 main cells, plus executed rank and 50-replication boundary checks. The source-driven TV/KL supplement was specified after core outcomes were inspected by analysis and before its own outcomes were known; it is a score comparison under the shared predictor, not a replication of the prior work's full pipeline.

From the combined delivery root, after analysis results exist:

```sh
python3 -m pip install -r presentation/environment.txt
python3 presentation/render.py --summary-dir results/main_summary --output-root . \
  --source-commit FULL_ANALYSIS_COMMIT --stage confirmatory
python3 presentation/supplement.py --results-root results --output-root . \
  --source-commit FULL_ANALYSIS_COMMIT
python3 presentation/manifest.py --source-root results --output-root . \
  --source-commit FULL_ANALYSIS_COMMIT
```

Use the full analysis commit recorded in the existing manifest. Rendering is a CPU task; allow about one minute (a planning allowance, not an experimental runtime). Exact library versions are pinned in `environment.txt`. No external data or API is needed. Generators consume supplied estimates/intervals and replication records; they do not rerun the experiments or re-estimate inference. Main display alpha is fixed at .1. Stage `diagnostic` may be used on pilot inputs only outside delivered paths.

| Asset stem | Generator | Supplied input and purpose |
|---|---|---|
| `joint_coverage` | `render.py` | `results/main_summary/summary.csv`; iid joint coverage, K=3/10, ncal=499, both noise scenarios |
| `group_shift_coverage` | `render.py` | Same; observed-group iid coverage and shifted marginal coverage, heterogeneous |
| `simplex_area` | `render.py` | Same plus `paired_contrasts.csv`; iid K=3 area and paired differences, both noise scenarios |
| `replication_variability` | `render.py` | `replications.csv`; finite-test coverage ECDFs at K=3, ncal=99/499, heterogeneous iid |
| `main_summary`, `k*_n*`, `all_estimates.csv` | `render.py` | Exact main-cell and full-grid values and pointwise intervals; all group-0 values remain in CSV |
| `oracle_shift` | `supplement.py` | Main summary/paired contrasts; shifted marginal/group1 coverage, shifted K=3 area and oracle paired differences |
| `boundary_targets`, `boundary_estimates.csv` | `supplement.py` | `results/boundary_summary/summary.csv`; transformed and original-target inverse-image coverage versus direct original-response membership |
| `prior_score_area` | `supplement.py` | Main paired contrasts; TV/forward-KL minus Euclidean/maximum/Aitchison, K=3, ncal=499, both mechanisms and environments |
| `paired_method_estimates.csv`, `area_precision.csv` | `supplement.py` | All supplied paired method comparisons and candidate-resolution diagnostics; unresolved orderings remain unresolved |
| `pullback_equivalence.csv` | `supplement.py` | Supplied exact event identity for original-target inverse-image coverage; copies measured transformed coverage, no new simulation or area estimate |
| `rank_checks` | `supplement.py` | `results/rank_checks.csv`; continuous/tied-score finite-rank coverage and variance checks |
| `calibration_tails`, `calibration_diagnostics.csv` | `supplement.py` | Main diagnostics; descriptive finite-test lower tails and supplied Wilson intervals |
| `paired_shift_estimates.csv` | `supplement.py` | Main shift contrasts; paired shifted-minus-iid estimates |
| `paired_epsilon_estimates.csv`, `zero_prevalence.csv` | `supplement.py` | Boundary epsilon contrasts/prevalence; paired replacement changes and exact-zero frequency |

Each figure has a vector PDF, inspection PNG and owner-authored `_caption.tex`. Each TeX table panel has a caption input; full-cell filenames encode their condition. Use, for example, `\caption[Joint coverage]{\input{figures/joint_coverage_caption.tex}}`; the optional short caption avoids fragile file input in the list-of-figures write. Table captions go above tables; figure captions below. Use `booktabs`, and `longtable` for `rank_checks.tex`; numeric table contents fit the official 5.5-inch text width at `\small`. Do not shrink venue margins. The compact main numeric panel and group/shift plot are the main priorities; the area plot shows all ten methods and six paired contrasts. Complete iid coverage, variability, oracle details, rank and boundary assets can go in the appendix subject to the manuscript's claims.

The 95% t intervals describe independent-replication means, not the distribution of individual calibrated runs; they are pointwise, not simultaneous. Method and environment differences use supplied paired intervals. Uniform Euclidean simplex area is a chosen reference measure at K=3, not a universal utility measure; no K=10 cross-geometry area ordering is supplied. TV exactly duplicates raw maximum at K=3 and is distinct at K=10; KL is forward y||prediction. Direct original-target clr diagnostics reject boundary points and have no nominal guarantee; original-target inverse-image regions have exactly the measured transformed coverage by event identity, including zeros, but their area was not estimated; the transform is max-and-reclose, not additive smoothing. Oracle ratios are known from the generator and do not demonstrate learned-ratio robustness. See `inspection.md` for completed visual checks and `artifact_manifest.json` for exact per-artifact data/code provenance.
