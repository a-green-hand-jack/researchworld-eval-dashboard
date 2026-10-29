# Review record: version 1 (paper-repo pull request #8)

- Head inspected: `e2f30f3` (contents of `main`, merged from `paper-repo`#5).
- Inspected: `workspace/pred_programs/pred_compound_filter.py`, `workspace/pred_results/compound_filter_results.txt`, `REPORT.md`.

## Checks

- Program rerun on the frozen inputs (RDKit 2026.09.1) writes 1345 lines, byte-identical to the delivered results file (sha256 `bad3cea5…`).
- Independent recount: PAINS 121, Brenk 1395, PAINS-or-Brenk union 1436, similarity removed 860, kept 1345. Matches the report.
- Every kept SMILES is a `hits.csv` row; no hit or active fails to parse.
- The program and report use the Morgan radius 2, 2048-bit Tanimoto fingerprint and the strict keep rule (max similarity < 0.5), as the plan states.

## Finding (open, requests changes)

- The output keeps 3 duplicate SMILES lines (3 extra rows; 1342 distinct of 1345). `REPORT.md` does not state the duplicate rule. The plan (`story-repo`, commit 0aa8a72) requires the method to state how duplicate hit SMILES are handled. Fix: state the rule in `REPORT.md` (keep one line per `hits.csv` row, or de-duplicate), and say which of the three SMILES it affects.

## Not checkable from this position

- The report's statement that `experiment-repo`'s program gives a byte-identical output is not checked here (code of `experiment-repo` is not readable by this position).
- `experiment-repo` commit e7e385c ("Output canonical SMILES") is not in this pull request's head. The next version must say which output form (input string or canonical) it delivers.
