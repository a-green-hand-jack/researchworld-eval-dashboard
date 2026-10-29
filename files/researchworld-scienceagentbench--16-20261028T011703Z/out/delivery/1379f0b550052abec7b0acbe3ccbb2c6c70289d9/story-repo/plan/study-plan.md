# Study plan: compound filter

Division (proposed in paper-repo PR #2, `.forgejo/CODEOWNERS`):
- `workspace/pred_programs/pred_compound_filter.py` -> experiment-repo
- `workspace/pred_results/compound_filter_results.txt` -> experiment-repo
- `.forgejo/CODEOWNERS` -> story-repo
- No figure, table or report is required by the objective: figtab-repo and paper-repo deliver no path unless the objective is revised.

Method (fixed here, to be used by experiment-repo):
1. Input: `hits.csv` and `train.csv` from `/initial-state/inputs/1/benchmark/datasets/compound_filter/`. Read `train.csv` with encoding `utf-8-sig` (BOM).
2. Parse each SMILES with RDKit `Chem.MolFromSmiles` (default sanitisation, no extra standardisation). Unparseable SMILES are dropped and counted in the run log, never kept.
3. Actives: rows of `train.csv` with `ACTIVITY == 1`.
4. Fingerprint: Morgan, radius 2, 2048 bits, chirality off (`GetMorganFingerprintAsBitVect`).
5. Similarity: Tanimoto (`DataStructs.BulkTanimotoSimilarity`). A hit is kept only if its maximum similarity over all actives is strictly below 0.5.
6. Filter: drop hits matching any RDKit `FilterCatalog` entry of PAINS (A, B, C) or BRENK.
7. Output: canonical SMILES of kept hits, one per line, in input order, to `workspace/pred_results/compound_filter_results.txt`.
   Duplicates: one line per distinct kept molecule, at the first occurrence of that molecule in input order. A molecule that appears in several kept rows of `hits.csv` is one compound, so it is written once. The run log also records the number of kept rows and the number of distinct molecules.

Evidence: each count (input, parse failures, PAINS/Brenk drops, similarity drops, kept) is recorded in the run log with the input file hashes.
