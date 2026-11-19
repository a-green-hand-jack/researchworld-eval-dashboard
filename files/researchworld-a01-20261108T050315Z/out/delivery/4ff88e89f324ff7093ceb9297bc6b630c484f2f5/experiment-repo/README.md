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
- `results/` — CSV outputs; `logs/` — run logs.

Status: work in progress; see issue #2 for the commitment and the wiki/issues for results.
