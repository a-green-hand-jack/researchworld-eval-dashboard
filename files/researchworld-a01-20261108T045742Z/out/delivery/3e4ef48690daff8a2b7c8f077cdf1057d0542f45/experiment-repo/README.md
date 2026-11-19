# experiment-repo — minimum targeted investment to top a multi-task leaderboard

Analysis code for: *how much targeted investment (raising a target model's scores on chosen sub-datasets) is needed to make it
rank first, as a function of the aggregation rule?*

Layout
- `src/fetch_helm.py` — download HELM MMLU v1.13.0 release summaries (SHA-256 manifest written next to the files).
- `src/build_data.py` — builds `data/processed/{ollb6.csv,helm_mmlu57.csv,...}` from the Open LLM Leaderboard `contents` parquet
  (commit `9c09a7cae43334062a82cb164f2ef255013dafa2`, file sha256 in `data/processed/manifest.json`) and the HELM files.
- `src/mti/scorerules.py` — exact minimum-investment solvers for score rules (mean, geometric/harmonic mean, median, min, trimmed mean).
- `src/mti/ordinal.py` — exact MILP solvers for rank rules (Borda, Condorcet winner, plurality).
- `src/run_core.py` — experiment driver (tidy CSV out). `tests/` — solvers vs brute force (`python3 -m pytest tests`).
- `src/run_robust.py`, `src/summarize_*.py`, `src/theory_checks.py`, `src/condorcet_existence.py` — robustness drivers, summaries, theory checks (script -> output map in REPRODUCE.md).
- `results/` — CSV outputs; `logs/` — run logs.

Status: analysis complete for the plan's claims C1-C8 except the items listed under "Not done" in RESULTS.md. Reproduction: REPRODUCE.md; results hand-off: RESULTS.md.
