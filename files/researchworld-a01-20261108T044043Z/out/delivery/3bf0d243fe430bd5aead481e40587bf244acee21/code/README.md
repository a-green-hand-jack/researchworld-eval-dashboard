# experiment-repo — minimum targeted investment to top a multi-task leaderboard

Analysis code for: *how much targeted investment (raising a target model's scores on chosen sub-datasets) is needed to make it
rank first, as a function of the aggregation rule?*

Layout
- `code/fetch_helm.py` — download HELM MMLU v1.13.0 release summaries (SHA-256 manifest written next to the files).
- `code/build_data.py` — builds `data/processed/{ollb6.csv,helm_mmlu57.csv,...}` from the Open LLM Leaderboard `contents` parquet
  (commit `9c09a7cae43334062a82cb164f2ef255013dafa2`, file sha256 in `data/processed/manifest.json`) and the HELM files.
- `code/mti/scorerules.py` — exact minimum-investment solvers for score rules (mean, geometric/harmonic mean, median, min, trimmed mean).
- `code/mti/ordinal.py` — exact MILP solvers for rank rules (Borda, Condorcet winner, plurality, Copeland).
- `code/run_core.py` — experiment driver (tidy CSV out). `code/tests/` — solvers vs brute force (`python3 -m pytest code/tests`).
- `results/` — CSV outputs; `results/logs/` — run logs.

Other scripts: `code/run_all.sh` (everything, in order), `code/run_minimal.sh` (minimal reproduction path), `code/mti/ordinal_lean.py`
(memory-lean Borda/Condorcet MILPs for the full board), `code/cap_evidence.py`, `code/ordinal_sample.py`, `code/run_leaf.sh` and the leaf pipeline.
`REPRODUCE.md` gives the environment, data checksums, seeds, measured run time and the script-to-table list; `results/README.md` describes each result file.
