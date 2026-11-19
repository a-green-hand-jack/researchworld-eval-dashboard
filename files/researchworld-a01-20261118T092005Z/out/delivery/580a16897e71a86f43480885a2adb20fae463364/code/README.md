# Code for "the price of first place on a multi-task leaderboard"

Everything in `results/` of the delivery and every number in the paper is produced by the scripts here from public score tables.
No model is trained or evaluated; the task is pure analysis of published leaderboard scores on CPU.

Layout (all paths relative to this directory, `code/` of the delivery):

| path | what |
|---|---|
| `lbprice/rules.py` | the seven aggregation rules and the "is first" test |
| `lbprice/solvers.py` | exact price solvers per rule (closed form / sorting / DP / MILP with HiGHS) with a breadth-constrained variant (`kmax`) and `frontier()` |
| `lbprice/e1.py`, `lbprice/e2.py`, `lbprice/boards.py` | price per target (E1/E3), m-experiment (E2), board loaders |
| `scripts/fetch_*.py`, `scripts/prep_*.py` | data download and preparation (checksums are recorded) |
| `scripts/run_*.py` | the experiments (one raw CSV each, written to `results/` here, `results/raw/` in the delivery) |
| `scripts/make_results.py` | raw runs to the result tables of `results/` (schema of `figtab-repo/DATA_CONTRACT.md`) |
| `analysis/` | statistical tests (R1-R5, cluster bootstrap) and model fits |
| `tests/` | brute-force verification of every solver |
| `REPRODUCE.md` | environment, data versions, seeds, commands, runtimes, script for each figure and table |

Quick start: install the packages listed in `REPRODUCE.md` (numpy, scipy, pandas, pyarrow, scikit-learn, highspy), then `python3 -m tests.test_bruteforce` (solver checks, minutes) and
the commands of `REPRODUCE.md` in the order given there. All paths are relative to this directory; raw run files of the delivery are in `../results/raw/`, the result tables and `headline.json` in `../results/`.
Anonymity: no author or institution names occur in code or data; the data sources are public (HELM release, Open LLM Leaderboard dataset snapshots) and are cited by version in `REPRODUCE.md`.
Limits of the exact solvers (sizes, optimality gaps, verification) are in `REPRODUCE.md` and in `results/headline.json` (`solver_gaps`, `solver_check`).
