# Review record: version 2 (paper-repo pull request #13)

- Head inspected: `c368bf4` (`main` at 69ac6d8, plus the CODEOWNERS split from PR #2; the diff between them is only `.forgejo/CODEOWNERS`).
- Inspected: `workspace/pred_programs/pred_compound_filter.py`, `workspace/pred_results/compound_filter_results.txt`, `REPORT.md`, `.forgejo/CODEOWNERS`.

## Checks

- Program rerun on the frozen inputs (environment variables for the paths; the program takes none as arguments): 3641 hits read, 512 actives parsed, 0 unparseable; 3520 after PAINS (A, B, C); 2205 after PAINS and Brenk; 1345 kept rows; 1337 distinct. Output is byte-identical to the delivered file, which has 1337 lines.
- PAINS A, B, C flags the same 121 hits as the full PAINS catalogue.
- Output is exactly the first-occurrence de-duplication of the kept canonical SMILES (one line per distinct molecule). Every line is canonical.
- Duplicate counts among kept rows match `REPORT.md`: 7 molecules, counts 3, 2, 2, 2, 2, 2, 2.
- Every output line is a `hits.csv` molecule (canonical form).
- CODEOWNERS assigns the program and the results to `experiment-repo`, and the report to none: the report is paper-repo's own path.

## Findings (open, requests changes)

1. `REPORT.md` line 4 says the output is "1345 canonical SMILES, one per line". The file has 1337 lines; 1345 is the kept row count. Fix the header to 1337.
2. `REPORT.md` line 39 says the program in `main` "is superseded" and that "until [PR #7] merges, `main` does not meet the rule." That is stale: `main` (69ac6d8, merged from PR #12) already has the canonical, one-line-per-distinct-molecule program, and I verified it meets the rule. Remove the sentence or correct it to say the verified version is in `main`.

## Not checkable from this position

- Line 45 says `experiment-repo`'s PR #7 gives the same 1345 kept rows. I cannot read that repository's code; the claim is not checked here.

## Re-review at head 8a42fa5 (approved)

- Program and output at `8a42fa5` are byte-identical to the versions verified above (sha256 `a9da811e…` program, `91c8c07e…` output, 1337 lines).
- Finding 1 fixed: the header now says 1337 canonical SMILES, one per distinct kept molecule.
- Finding 2 fixed: the report now says `main` (PR #12) already writes the rule's output.
- Still not checked here: line 45's claim about PR #7 (experiment-repo's code is not readable by this position). It does not change the delivered output.
- Conclusion: approved; the delivered program and results meet the objective and the study plan's output rule.
