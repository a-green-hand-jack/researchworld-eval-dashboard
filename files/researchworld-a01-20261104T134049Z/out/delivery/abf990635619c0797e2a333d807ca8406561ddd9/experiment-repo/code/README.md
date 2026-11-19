# code/ — minimum targeted investment to top a multi-task leaderboard

Analysis code for: *how much targeted investment (raising a target model's scores on chosen sub-datasets) is needed to make it
rank first, as a function of the aggregation rule?* Everything is reproduced by `bash code/run_all.sh` from the repository root
(commands, data versions and checksums, seeds, run times and the map from each paper figure/table to its scripts: `REPRODUCE.md`).

Layout
- `fetch_ollb.py`, `fetch_helm.py` — pinned downloads (Open LLM Leaderboard `contents` commit `9c09a7ca…`, HELM MMLU v1.13.0) with SHA-256 checks.
- `build_data.py`, `ollb_items.py` — model x task score matrices in `data/processed/` and the item counts used for evaluation noise.
- `mti/data.py` — loading, cap definitions (`ceil`, `front0`, `gainH`, `emp99`, `emp99T`, `emp99P`); `mti/scorerules.py` — exact solvers for
  score rules (mean, power/geometric/harmonic, median, trimmed mean, min); `mti/ordinal.py` — exact MILPs for Borda, Condorcet winner,
  plurality, Copeland; `mti/weighted.py` — weighted mean; `mti/theory.py` — closed forms P1-P3.
- `run_core.py` (grid over cap x rule x target), `run_robust.py` (evaluation noise, task bootstrap, task subsets), `run_weights.py`,
  `run_zcost.py`, `run_margin.sh` — experiments; raw outputs go to `results/runs`, `results/robust`, `results/variants`.
- `theory_check.py`, `official_rules_check.py` — P1-P3 against the solvers; the leaderboards' published aggregate against our mean.
- `assemble_core.py`, `summarize*.py`, `frontier.py`, `paired.py`, `make_tables.sh` — core tables and summaries in `results/` and `results/summary/` (schema: `results/README.md`).
- `tests/` — each solver against brute force or an independent LP (`python3 -m pytest code/tests`).

Run logs of our own runs were not kept in the delivery (they are not needed to reproduce a result).
