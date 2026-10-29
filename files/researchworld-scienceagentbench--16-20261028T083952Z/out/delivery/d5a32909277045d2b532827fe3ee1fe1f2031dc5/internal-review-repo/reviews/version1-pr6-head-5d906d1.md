# Review of paper-repo#6 (Version 1), head 5d906d1

## Inspected
- PR head `version/1` at 5d906d1 ("Correct the report: 39312 training rows, 1345 provenance, verbatim sensitivity output"). Against `main` (0a4bb36) the only change is `report.md`; `workspace/` is byte-identical to `main`.
- Earlier record (71ad5fe) found the head missing the required paths; that is fixed at this head.
- Program: run at `main` with `python3 -I` (RDKit 2026.09.1, Python 3.11.2), output byte-identical to `workspace/pred_results/compound_filter_results.txt`, 1342 lines.
- Independent recount from the inputs: 3641 hits, 2205 after PAINS A/B/C and Brenk, 512 actives, 1345 kept before deduplication, 1342 distinct.
- Sensitivity rows checked independently: Morgan r1 gives 1194/1193; Morgan r2 at 0.45 gives 1279/1277. Both match the report.
- Report claims: `train.csv` is 39312 data rows (matches DictReader); the 1345 count is attributed to `analysis/sensitivity.py` (experiment-repo, 60fad5a), which is not in the tree.

## Conclusion
Approved. The required paths exist and are nonempty, the results reproduce from the inputs, and the report's figures match my recount.

## Residual note (not a blocker)
The verbatim sensitivity output cites `analysis/sensitivity.py` at experiment-repo's commit 60fad5a. The script is not in the delivered tree, so the sensitivity table rests on that provenance rather than on a rerun from the delivery. I checked two rows and they agree. The last line of the verbatim output ("program re-run equals committed results file: True 1345") is ambiguous: the 1345 is the pre-deduplication count, not a file comparison. The report could say so.
