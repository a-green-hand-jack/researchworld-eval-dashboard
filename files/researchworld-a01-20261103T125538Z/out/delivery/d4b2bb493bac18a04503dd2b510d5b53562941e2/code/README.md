# Exact task investment on frozen multitask leaderboards

This repository owns the analysis, code, data provenance and numerical evidence for the research objective in issue #1. It does not contain the organization's final manuscript or publication figures. The settled study plan assigns the full analysis package to `code/` in the paper delivery (world/story-repo#2; paper CODEOWNERS).

The model is a **conditional score intervention**: select tasks for one target entry, raise its scores to an explicit ceiling (or a fraction of remaining headroom), keep all opponents' raw scores fixed, recompute the ranking, and minimize task count. This is not a measurement of actual training data, compute, or contamination effects. See `notes/DATA_AND_MODEL.md` and `notes/PRIMARY_FINDINGS.md`.

## Data and environment

- HELM MMLU release v1.13.0, release date 2025-01-10: 79 complete entries × 57 subjects.
- Open LLM contents commit `9c09a7cae43334062a82cb164f2ef255013dafa2`, snapshot date 2025-03-20: 4,576 complete entries × six tasks, with one flagged entry excluded from primary analysis.
- URLs, SHA-256 checksums, acquisition time and file sizes: `data/manifest.json`.
- Input audits: `results/data_audit.json`; installed versions: `results/environment.json`.
- No account, model training, model inference or GPU is required. Public score datasets have no separate declared data license; this repository does not infer data rights from HELM's code license or model metadata. Raw downloads remain outside Git under `data/raw/`.
- No literature search has been performed by this analysis position, and no forbidden study material has been accessed.

The existing research environment provides NumPy, SciPy (with HiGHS MILP), pandas, PyArrow and Python. Exact installed versions are recorded; install those versions in a clean environment using `requirements.txt`.

## Reproduce

Run from this analysis directory: the repository root in the standalone analysis repository, or `cd code` from the integrated paper delivery root. Acquisition requires HTTPS; subsequent commands are CPU-only and offline. Limit BLAS/OpenMP threads on shared hosts:

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
python3 src/acquire.py
python3 src/prepare.py
python3 -m unittest discover -s tests -v
python3 src/run_bundle.py helm
python3 src/run_bundle.py openllm
python3 src/random_baseline.py --board helm --repeats 2000
python3 src/random_baseline.py --board openllm
python3 src/task_subsets.py --repeats 200 --tasks 45
python3 src/weighted_mean.py
python3 src/audit_normalization.py
python3 src/summarize.py
python3 src/validate_outputs.py
python3 src/validate_mc_precision.py
```

In this research environment computations that outlive a turn use `ht-resource run local-compute --cwd "$PWD" -- env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 -u <script> ...`. Snapshot bundles can run independently in parallel when resources permit. Do not run the same bundle twice concurrently into the same output paths.

Allocated resources, unmeasured peak memory and the labeled full-reproduction estimate are in `notes/COMPUTE_AND_REPRODUCTION.md` and `results/compute_configuration.json`: 2 logical CPUs, 4 GiB, no GPU; allow 20 minutes with dependencies installed, or 30–60 minutes for a new environment including installation/downloads (planning estimates, not measured end-to-end times). Measured pilot timings and planning estimates are in `notes/RUN_SIZING.md`; completed bundle runtimes are in `results/runtimes_*.json`. Per-target solver runtime is retained in every attack row. Random seeds are 519733 for random task orders, 449027 for distinct-task subsets, and 7821/999/112 for small optimization verification tests. Primary optimizations are deterministic; tied optimizer solutions can select different equally optimal task subsets across solver versions.

## Numerical source map

- `src/acquire.py` → raw public tables and `data/manifest.json`.
- `src/prepare.py` → `data/processed/*.csv` and `results/data_audit.json`.
- `src/attacks.py` → exact optimizers, used by all runs; `tests/test_attacks.py` independently verifies small cases.
- `src/run_bundle.py` / `src/run_experiments.py` → per-target primary/sensitivity attack CSVs, checkpoint logs and completed runtime records.
- `src/summarize.py` → `results/primary_summary.csv`, `paired_rule_comparisons.csv`, `rank_strata.csv`, `budget_success_curves.csv`, `sensitivity_summary.csv`.
- `src/random_baseline.py` → `results/random_baseline_{helm,openllm}.csv`. Six-task probabilities are exact; HELM uses 2,000 shared random orders per target. Wilson intervals concern success probabilities. `results/random_mean_mc_targets_helm.csv` retains stopping-cost sample variances, and `random_mean_mc_summary_helm.csv` reports marginal across-target Monte Carlo standard errors/normal-approximation 95% intervals. See `notes/RANDOM_BASELINE_MC_ERROR.md`. Reproduce only these sidecars while checking the archived baseline with `python3 src/random_baseline.py --board helm --repeats 2000 --mc-error-only`.
- `src/task_subsets.py` → `results/task_subsets_helm.csv` and `_summary.json`. All entries share each 45-subject subset. Central 95% ranges describe the random-subset perturbation distribution, not confidence coverage for future benchmarks or evaluation-item noise.
- `src/audit_normalization.py` → `results/normalization_rank_audit.json`, ranks/ties before and after normalization.
- `src/validate_outputs.py` → `results/analysis_validation.json`, full-run completion, status counts and output hashes.
- `src/weighted_mean.py` → `results/weighted_mean_helm.csv`, a count-weighted aggregation sensitivity while retaining task-count investment cost.

The figure owner will generate publication figures from these numerical sources and record the final figure-to-script map in the paper delivery. The paper owner will build the PDF/LaTeX and checklist under the agreed venue requirements.

## Interpretation and limitations

Equal-subject mean and count-weighted mean are different rules. Geometric means use actual zeros, without pseudocounts; their origin/normalization dependence is tested with raw Open LLM scores. Borda uses half credit for tied pairs and recomputes opponents' rank losses. Its competitor-pool dependence is tested using exact-score-vector and fullname deduplication. Duplicated fullname representatives are chosen by lexicographic entry identifier, not by best performance. Missing scores are not imputed.

A score ceiling is a modeling assumption. Full perfect-score saturation is an optimistic bound on the number of affected tasks under no cross-task transfer and no score reduction. It does not lower-bound the number of training datasets when one investment transfers to other tasks. Observed-frontier saturation is a distinct assumption, not evidence that every target can achieve each frontier score. Partial uplift can make winning infeasible; report success fractions instead of treating the conditional cost among successful targets as overall ease. No rule-resistance ordering is universal.
