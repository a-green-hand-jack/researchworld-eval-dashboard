# Compound filter: delivered tree

This tree reproduces the compound-filter results (1342 SMILES) from the
task's dataset. Start from the report, `report.md`.

## Contents

- `report.md`: method, results, sensitivity and decisions.
- `workspace/pred_programs/pred_compound_filter.py`: the filter program.
- `workspace/pred_results/compound_filter_results.txt`: the kept SMILES, one per line (1342 lines).
- `workspace/pred_results/run_log.txt`: the log of the run that produced the results file.

## Reproduce

Requirements: Python 3.11 and RDKit 2026.09.1 (the version the results were
made with).

    pip install rdkit==2026.09.1
    python3 -I workspace/pred_programs/pred_compound_filter.py

The program reads `/benchmark/datasets/compound_filter/hits.csv` and
`train.csv` (paths are hard-coded in the program). It writes
`compound_filter_results.txt` to `/workspace/pred_results/` by default. To write
elsewhere, set `PRED_RESULTS_DIR`:

    PRED_RESULTS_DIR=/tmp/out python3 -I workspace/pred_programs/pred_compound_filter.py

A successful run prints `after_similarity: 1342` and `Wrote 1342 SMILES`, and the
output file has 1342 lines. Compare with the delivered file:

    cmp /tmp/out/compound_filter_results.txt workspace/pred_results/compound_filter_results.txt

The sensitivity analysis in the report is not part of this tree; its variants
are defined in the report's Sensitivity section.
