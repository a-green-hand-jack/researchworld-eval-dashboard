# Minimum targeted investment on public multitask leaderboards

Reproducible analysis for the research question: how much score-space investment
is needed to make a fixed model uniquely first, and how does this depend on the
aggregation rule? This is an analysis component; the manuscript and rendered
figures are owned by the paper and presentation positions.

**Status:** see [current completion and failures](docs/RUN_STATE.md).
HELM and OLLB score main runs and all declared uncertainty/control runs are
complete, including matched OLLB ordinal and all final-review additions. The original
16-file independent clean recomputation passed all457,772 rows within1e-5
absolute tolerance (maximum finite difference5.8069e-9); the review/final
extensions have separate passing clean records. Results under
`results/checkpoint_archive/` are explicitly superseded/partial. No incomplete
file should be used as a final empirical claim. Each new main/robustness CSV
has a `.meta.json` with input/code hashes, arguments, elapsed time and completion
flag. Legacy `ollb_closed.csv` is a completed checkpoint ceiling score-rule run.

- [Protocol and interpretation](docs/PROTOCOL.md)
- [Reproduction contract and seeds](docs/REPRODUCTION.md)
- [Data provenance and permissions](docs/DATA.md)
- [Propositions and proof notes](docs/THEORY.md)
- Commitment: experiment-repo issue2.

Python3.11.2, CPU only; exact measured dependencies are in `requirements.lock`.
Set `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` (the Makefile and suites do this).

```
python3 -m pip install -r requirements.lock
make validate test             # uses bundled processed public score tables
make data                      # optional full re-download and rebuild
MTI_MILP_TIME_LIMIT=1200 make -j2 main  # two independent main suites
make robustness baselines review-checks tables final-additions
```

`make all` runs the full analysis from bundled processed data. `make data` needs
anonymous HTTPS access to the two public sources. No model training, GPU or
paid API is used. Raw sources are intentionally not vendored. Measured extension
runtimes are in `docs/FINAL_EXTENSION_FINDINGS.md`; original full-study clean
stage timings and the preserved timeout are in `docs/REPRODUCTION.md`. The initial timed pilot is
`results/pilot.csv`. Interrupted runs remain incomplete in metadata and can
be restarted; main driver supports `--resume` only with identical inputs/code
and parameters (caller responsibility).

Core modules: `src/mti/scorerules.py` (closed forms, water-filling, order statistics,
trimmed-mean MILP), `src/mti/ordinal.py` (Borda/Condorcet/plurality MILPs, finite-level
Linf search), `src/mti/data.py` (frame/cap definitions). Tests compare optimizers
with independent brute force, LP and convex optimization. Solver limits/errors
are raised separately from proven infeasibility.
