# experiment-repo — minimum targeted investment to top a multi-task leaderboard

Analysis code for: *how much targeted investment (raising a target model's scores on chosen sub-datasets) is needed to make it
rank first, as a function of the aggregation rule?* Start with `REPRODUCE.md` (environment, data checksums, seeds, commands, claim-to-file map).

Layout
- `run.sh` — entrypoint, one target per experiment (`sh run.sh <target>`).
- `src/fetch_ollb.py`, `src/fetch_helm.py`, `src/build_data.py`, `src/ollb_items.py` — pinned downloads and the processed score matrices (`data/processed/`).
- `src/mti/scorerules.py` — exact solvers for score rules (mean, geometric/harmonic/power mean, weighted mean, median, min, trimmed mean) and Linf bisection.
- `src/mti/ordinal.py` — exact MILP solvers for rank rules (Borda, Condorcet winner, Copeland, plurality).
- `src/run_core.py` (main grids), `src/run_robust.py` (evaluation noise, task bootstrap, task-subset scaling), `src/theory_checks.py` (real-data checks), `src/example_plan.py` (explicit plan of one target), `src/analyze.py` (tables).
- `tests/` — solvers vs brute force, LP and SLSQP (`python3 -m pytest tests`).
- `results/` — grid CSVs, `results/tables/` summaries; `logs/` — run logs.

The large OLLB grids are committed as `results/*.csv.gz` (`ollb_score`, `ollb_wmean`, `ollb_nomerge_score`, `ollb_raw_score*`); `run.sh` writes them as plain CSV, `src/analyze.py` reads either. `results/FINDINGS.md` states the finding per claim.
