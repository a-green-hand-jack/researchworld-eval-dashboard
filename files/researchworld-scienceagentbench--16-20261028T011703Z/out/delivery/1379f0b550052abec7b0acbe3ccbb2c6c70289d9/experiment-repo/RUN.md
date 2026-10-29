# Run record: compound filter (analysis working note, not delivered)

Program: `workspace/pred_programs/pred_compound_filter.py`
Inputs: `/benchmark/datasets/compound_filter/hits.csv` (3641 rows), `train.csv` (512 actives of 39311 rows).
Environment: RDKit 2026.09.1 in `/hutian/.venv` (installed with `pip install rdkit`), Python 3.

Stage counts (primary run):
- hits read 3641; unparseable 0
- actives parsed 512 (unparseable 0)
- passing PAINS A/B/C: 3520; passing Brenk: 2246; passing both: 2205
- kept after max Tanimoto < 0.5 (Morgan r=2, 2048 bits): 1345

Output: `workspace/pred_results/compound_filter_results.txt`, 1345 lines.

Robustness (count kept by fingerprint and threshold, same PAINS/Brenk step, `robustness.py` not delivered):

| fingerprint | t 0.40 | 0.45 | 0.50 | 0.55 | 0.60 |
|---|---|---|---|---|---|
| Morgan r2 2048 bits (primary) | 1256 | 1279 | 1345 | 1467 | 1603 |
| Morgan r3 2048 bits | 1300 | 1360 | 1448 | 1603 | 1705 |
| Morgan r2 count | 1184 | 1273 | 1345 | 1493 | 1633 |
| FCFP r2 2048 bits | 1023 | 1175 | 1293 | 1400 | 1539 |
| Atom pair 2048 bits | 821 | 1137 | 1288 | 1482 | 1614 |

Reading: the kept count moves by about 4% to 9% with the fingerprint at the stated threshold, and by about 5% per 0.05 of threshold. The primary result is one of several defensible choices, not a unique answer.

## Revision to the study plan (story-repo `plan/study-plan.md`, 0aa8a72)

- Output is canonical SMILES (`Chem.MolToSmiles`), in input order, one per kept hit row. The raw input text differs from canonical form for 1327 of the 1345 lines.
- The output has 1345 lines but 1337 distinct SMILES: 8 kept rows are duplicate structures in `hits.csv`. They are kept as separate rows, as the plan says, not de-duplicated.
- Every output line is a canonical form of a hit, and parses.
- PAINS and Brenk are counted as separate stages: after PAINS 3520, after PAINS and Brenk 2205.
- Input hashes (sha256): hits.csv `89311c62...552b`, train.csv `4fcfc9cc...c13a1`. Run log: `run.log` in the working directory, copied alongside the output.

## Duplicate rule (story-repo, 56276ba): one line per distinct molecule

- 1345 kept rows, 1337 distinct molecules. The output writes each molecule once, at its first occurrence in input order: 1337 lines, all distinct, all canonical forms of hits, all parse.
- The earlier 1345-line output is superseded by this one.
