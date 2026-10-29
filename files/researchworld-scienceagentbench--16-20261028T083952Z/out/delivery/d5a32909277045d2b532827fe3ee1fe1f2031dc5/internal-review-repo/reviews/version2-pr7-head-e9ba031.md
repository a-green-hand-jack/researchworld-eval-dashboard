# Review of paper-repo#7 (Version 2), head e9ba031

## Inspected
- `version/2` at e9ba031 against `release` (e58b2e3): changes are `README.md` and `report.md` only. `workspace/` is byte-identical to `main`, so the program and results are unchanged from the version 1 I approved.
- Program reproduction at `main` (earlier, with `python3 -I`, RDKit 2026.09.1): output byte-identical to `compound_filter_results.txt`, 1342 lines.
- Input claims checked: `hits.csv` has 3641 rows and 3597 distinct SMILES; `train.csv` has one unparseable row, with ACTIVITY 0; 512 actives.
- Sensitivity rows, independently recomputed from the inputs with the variant definitions given in the report: r3 1448/1445; FCFP-like (Morgan r2 with feature invariants) 1293/1290; atom pair 1288/1287; r2 at 0.55 1467/1464; r2 at 0.45 1279/1277; r1 1194/1193. All match the report, and the baseline 1345/1342 matches my earlier recount.

## Findings against the four external issues (#3 to #6)
- #3 (1345 match claim): resolved. The report now states 1345 as the pre-deduplication baseline, not as a file match.
- #4 (sensitivity not reproducible): resolved. Each variant is defined in the report, and I could re-derive all seven counts from those definitions.
- #5 (reproduction instructions): resolved. `README.md` gives the RDKit pin, the run command, the output comparison and the dataset paths.
- #6 (unparseable row): resolved. The skip is stated as not conditioned on activity, and the skipped row's ACTIVITY 0 is stated as a direct check.

## Conclusion
Approved at e9ba031.
