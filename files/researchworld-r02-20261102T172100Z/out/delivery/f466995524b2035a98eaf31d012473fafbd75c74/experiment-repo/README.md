# Compositional-response conformal benchmark

Working analysis repository for ResearchWorld. `notes/analysis_design.md` describes the target and design. `analysis/benchmark.py` generates all input data and records per-replication coverage, subgroup coverage, thresholds and low-dimensional area estimates. `analysis/checks.py` checks finite-sample ranks, geometry invariance, coordinate nesting and a known simplex area.

Quick checks: `OPENBLAS_NUM_THREADS=1 python3 analysis/checks.py`.

Pilot: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 analysis/benchmark.py --output results/pilot.jsonl --reps 2`.

Only synthetic data are used, so no data download or account is required. The final replication commands, timings and frozen environment will accompany the full results. No prohibited paper, derivative, code or page has been accessed by this position.
