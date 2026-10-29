# Compound filter

Delivery for the task "filter the compounds in `hits.csv`" (see `workspace/`).

- `workspace/pred_programs/pred_compound_filter.py`: reads `/benchmark/datasets/compound_filter/{hits,train}.csv`
  and writes `workspace/pred_results/compound_filter_results.txt` (the task's `/workspace/pred_results/`).
- Filters: a compound is kept only if it matches no PAINS (A/B/C) or Brenk substructure (RDKit `FilterCatalog`)
  and its maximum Tanimoto similarity (Morgan radius 2, 2048 bits) to any `ACTIVITY == 1` compound in `train.csv` is below 0.5.
  Unparseable SMILES are dropped.
- Result: 1345 SMILES kept, one per line, out of the 3641 rows of `hits.csv` (the script prints this count when run).
  Per-filter counts overlap: 121 rows match PAINS, 1395 match Brenk, and 1423 have a maximum Tanimoto >= 0.5 to the 512 actives
  (independent recomputation by `internal-review-repo`).
- Duplicates: `hits.csv` has 3597 unique SMILES. The filter is applied per row and duplicates are retained,
  so the output has 1345 lines and 1342 distinct SMILES.
- Requires `rdkit` and `pandas`. Owner of the program and its output: `experiment-repo`.
