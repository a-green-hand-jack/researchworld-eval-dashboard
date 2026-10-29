# Review of paper-repo#5 (Version 1), head 664ebbc
Inspected: program, output (1345 lines), README, venue-artifacts.json at 664ebbc.
- Ran the program (rdkit pip, pandas): exits 0, prints "1345 of 3641 compounds kept", output byte-identical to delivered file.
- Independent recomputation (separate script, AllChem Morgan r2/2048, PAINS and Brenk catalogs separately, ACTIVITY==1 only, strict <0.5): 0 invalid SMILES; 121 PAINS, 1395 Brenk, 1423 with max-sim >=0.5; 1345 kept, same list in same order. Semantics supported.
- Defect: README says "3640 compounds in hits.csv"; hits.csv has 3641 data rows (file has no trailing newline; program output itself says 3641). 
- Note: hits.csv has 84 rows in duplicate SMILES groups (3597 unique); output keeps duplicates (1345 lines / 1342 distinct). Consistent with "filter the rows", but README should say so.
Conclusion: requested changes (README only); not yet approved.

## Re-review at 8d535bb (README-only change since 664ebbc)
README now states 3641 rows, 3597 unique SMILES, duplicates retained, and per-filter counts that match my recomputation. Program and output unchanged (verified earlier). Approved.

## Final (paper-repo#7 into final), head 8d535bb
Identical tree to the version approved above (no diff to 8d535bb); approved.
