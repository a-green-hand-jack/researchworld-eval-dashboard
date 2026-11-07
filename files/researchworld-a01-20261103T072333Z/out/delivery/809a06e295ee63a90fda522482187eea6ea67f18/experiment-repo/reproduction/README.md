# Reproduce the score-intervention study

Use Python 3.11+ with NumPy, SciPy (including `scipy.optimize.milp` / HiGHS), pandas and PyArrow. The actual environment is recorded in `environment.json`. CPU only. Set `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` to prevent oversubscription.

1. `python3 scripts/acquire.py` downloads 57 HELM subject summaries plus the release summary/listing and one pinned Open LLM parquet. Frozen version/commit, source URLs, acquisition date, byte sizes and SHA-256 checksums are in `data/manifest.json`. No question text, model weights, or private data is acquired. Existing files are hashed rather than downloaded again; every hash must match the delivered manifest, which is preserved. A mismatch aborts acquisition rather than silently accepting changed inputs.
2. `python3 scripts/prepare.py` produces audited complete matrices under `data/processed/`. HELM keeps all 79 models; Open LLM excludes the one source-flagged evaluation. Evaluations at different precisions remain distinct entries; a one-evaluation-per-fullname sensitivity is provided with deterministic lexicographic selection.
3. `python3 tests/test_solvers.py` checks optimizer correctness against independent exhaustive enumeration.
4. `python3 scripts/analysis.py --dataset helm --output results/attacks_helm.csv --random-reps 256`.
5. `python3 scripts/analysis.py --dataset open_llm --output results/attacks_open_llm.csv --random-reps 1`. For six tasks this flag requests an exact subset-based random-order baseline, not one sampled random order.
6. `python3 scripts/summarize.py` produces machine-readable descriptive summaries and curves. Figure/table generation belongs to the presentation owner's delivered scripts; this analysis produces their numerical inputs.

All stochastic runs use seed 20261103; solver validation uses seed 47. No model is trained or evaluated. Primary experiments modify only the target's published task scores, under the explicitly stated intervention law in `notes/methods.md`. A unit of cost is one selected task. It is not a dollar, training example, token, or compute unit; tasks have heterogeneous sizes.

`results/attacks_*.csv` stores every target, rule, gain setting, optimal subset, solver status, rank, cost and random baseline. Missing k with status `infeasible` means no allowable subset can achieve first place. `bounded` or `solver_failure` would mean unresolved computation and must not be counted as mathematical infeasibility. Random expectation uses n+1 as censoring when no random order succeeds. Pilot CSVs are timing/validation artifacts and are excluded from study summaries. Runtime pilot measurements and planning estimates are distinguished in `notes/pilot-validation.md`; completed full runtimes are recorded below.

Score-data licenses are not separately declared by upstream. The supplied code repository's Apache-2.0 license and model Hub License fields are not licenses for the score data. Acquisition is public, requires no account and uses only summary scores. This package asserts no upstream data license.

The objective prohibits accessing the existing paper on this specific question or material discussing it. This position used the frozen task files and public data endpoints only, performed no literature searches, and encountered none of that prohibited material. Literature context is supplied independently by its owner.

Additional completed robustness commands:

```bash
python3 scripts/analysis.py --dataset helm --output results/attacks_helm_strict.csv --strict
python3 scripts/analysis.py --dataset open_llm --output results/attacks_open_llm_strict.csv --strict
python3 scripts/analysis.py --dataset open_llm_raw --output results/attacks_open_llm_raw.csv --primary-only
python3 scripts/analysis.py --dataset open_llm_unique --output results/attacks_open_llm_unique.csv --primary-only
python3 scripts/robustness.py --dataset helm --reps 200
python3 scripts/robustness.py --dataset open_llm
python3 scripts/diagnostics.py
python3 scripts/summarize.py
```

Measured process times: full HELM primary 28.22s, Open LLM primary 71.41s, raw-score primary 12.80s, deduplicated-cohort primary 12.33s, 200 HELM bootstrap designs 135.95s, six Open LLM task deletions 23.39s. Strict-first and raw/unique jobs together used 70.868 CPU seconds; the composition job used 150.772 CPU seconds. Total tracked compute, including pilots and independent optimizer tests, was 316.972 CPU seconds on this shared host. These are measurements, not guarantees for other hardware. Internet acquisition time is separate.

The random stopping estimand is the full-cohort E[min(T,n+1)], including a known n+1 for each provably infeasible target. Success probability at the target-specific optimum is a separate reachable-only quantity, because an infeasible target has no optimum. Summary files report a nonnull denominator for each. `random_requested` and `random_baseline_method` distinguish missing computation from deterministic infeasibility; Monte Carlo intervals for full-cohort stopping means account for exact infeasible constants. Run `python3 tests/test_random_estimand.py` for an independent exhaustive infeasible-case/two-target denominator regression. Historical measured attack files were corrected without rerunning optimizers or drawing new random orders by `scripts/refresh_random_metadata.py`; fresh `analysis.py` runs already write the corrected values.

The settled primary comparison uses `results/challenger_budget_curves.csv`, `challenger_summary.csv` and `challenger_paired_rules.csv`: exclude the union of all five primary co-first incumbent winners once per score/rival design and keep that target set fixed across rules/gains/strict-win sensitivity. Full-cohort curves and summaries are labelled secondary. `random_baseline_aggregate_uncertainty.csv` now includes a `cohort` column (`full_cohort` or `common_challengers`); filter it explicitly when rendering a comparison. No optimizer or random draw changes when the cohort denominator changes.
