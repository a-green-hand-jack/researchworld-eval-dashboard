# Compound filter: PAINS/Brenk removal and dissimilarity to training actives

## Task

Filter the compounds in `hits.csv` and write the SMILES of those kept to
`pred_results/compound_filter_results.txt`, one per line. A compound is kept
when it has no PAINS or Brenk substructure match and its maximum Tanimoto
similarity to any active compound in `train.csv` is strictly below 0.5.

## Method

- **Inputs.** `/benchmark/datasets/compound_filter/hits.csv` (3641 rows) and
  `train.csv` (39312 data rows, one per line after the header; 512 with `ACTIVITY == 1` are the actives).
- **Structure filter.** PAINS A, PAINS B, PAINS C and Brenk catalogues from
  RDKit `FilterCatalog`. A compound with any match is removed.
- **Similarity.** Morgan fingerprints, radius 2, 2048 bits, Tanimoto
  similarity. A compound is kept when its maximum similarity to the 512
  actives is < 0.5.
- **Duplicates.** Each distinct surviving SMILES is written once, in
  first-occurrence order (see Decisions).
- **Software.** RDKit 2026.09.1, Python 3.11.2.

The program is `workspace/pred_programs/pred_compound_filter.py`. Its output is `workspace/pred_results/compound_filter_results.txt`.

## Results

| Stage | Count |
|---|---|
| Input compounds (`hits.csv`) | 3641 (3597 distinct SMILES) |
| Valid SMILES | 3641 |
| After PAINS and Brenk removal | 2205 (1436 removed) |
| Active training compounds used | 512 |
| Kept after similarity < 0.5, before duplicate removal | 1345 |
| Kept, distinct SMILES written | **1342** |

The program's run log, `workspace/pred_results/run_log.txt`, records the stages
from `input` to `after_similarity: 1342`. It does not record the 1345 count. The
1345 count is the baseline row of the sensitivity analysis below, which counts
hits before duplicate removal.

The results file is written by the program and has 1342 lines, with no
duplicate lines. Re-running the delivered program in a separate directory with
`python3 -I` and RDKit 2026.09.1 gave a byte-identical file.

## Sensitivity

The kept count depends on the fingerprint, radius and threshold. Each row is
the kept count for one variant, on the same 2205 compounds that pass the
PAINS and Brenk filter, with the same 512 active training compounds. "Kept"
counts rows before duplicate removal; "Distinct" counts distinct SMILES.

| Variant | Fingerprint | Threshold | Kept | Distinct |
|---|---|---|---|---|
| Baseline | Morgan, radius 2, 2048 bits | 0.5 | 1345 | 1342 |
| Radius 1 | Morgan, radius 1, 2048 bits | 0.5 | 1194 | 1193 |
| Radius 3 | Morgan, radius 3, 2048 bits | 0.5 | 1448 | 1445 |
| FCFP | Morgan with feature invariants (FCFP-like), radius 2, 2048 bits | 0.5 | 1293 | 1290 |
| Atom pair | Atom-pair fingerprint as bit vectors (not count vectors), 2048 bits | 0.5 | 1288 | 1287 |
| Threshold 0.45 | Morgan, radius 2, 2048 bits | 0.45 | 1279 | 1277 |
| Threshold 0.55 | Morgan, radius 2, 2048 bits | 0.55 | 1467 | 1464 |

The variants show that the kept count moves by about ±10% with the
fingerprint and threshold choices. Only the baseline is the task's
definition; the other rows are context, not alternatives chosen for the
result.

## Decisions

- **Duplicate removal.** The task asks for the SMILES of the kept compounds,
  one per line. Writing each distinct SMILES once gives 1342 lines; keeping
  every row gives 1345. The distinct form is used. The difference is 3
  compounds, and both counts are stated above.
- **Unparseable training row.** One training SMILES does not parse under RDKit
  (an aluminium sulfate-type salt), and the program skips it before it reads
  `ACTIVITY`. The skip is not conditioned on activity: an unparseable active would
  also be skipped. For this dataset the skipped row has `ACTIVITY` 0, which
  was checked directly from `train.csv` (the row is the only one whose SMILES
  fails to parse, and its label is 0). So the 512 actives and the results are
  unchanged by the skip.

## Reproducibility

See `README.md` for the run command, the RDKit pin and the dataset paths.

The independent check was run from the delivered program, not from a copy:

    PRED_RESULTS_DIR=<scratch> python3 -I workspace/pred_programs/pred_compound_filter.py

with RDKit 2026.09.1 and Python 3.11.2 in a separate directory. The output file
matched the delivered `compound_filter_results.txt` byte for byte, and the
run printed the stage counts in the Results table.
