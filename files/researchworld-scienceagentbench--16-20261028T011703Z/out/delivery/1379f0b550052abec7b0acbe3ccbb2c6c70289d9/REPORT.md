# Compound filter for hit triage: report

## Question and claim

Question: which of the 3641 screening hits in `hits.csv` should a chemist keep, if a hit is kept only when it carries no PAINS or Brenk substructure alert and is dissimilar to every known active in `train.csv`?

Claim: applying these two criteria to the hits leaves **1337 distinct molecules** (1345 kept rows, 7 molecules repeated). These are the hits that pass the stated criteria. They are not validated actives, and the filter does not predict activity. The alert lists are generic, so the criteria remove chemistry that might be real as well as chemistry that is not.

Significance: the report establishes only what this stated filter keeps from these hits and how sensitive that count is to its settings. It does not establish that such a filter is a standard or advisable triage step.

## Data

- `hits.csv`: 3641 rows, 3597 distinct raw SMILES, no unparseable structures.
- `train.csv`: 39312 rows; 512 with `ACTIVITY == 1` (the actives), 38800 with `ACTIVITY == 0`. No unparseable actives.
- Input files are read with the `utf-8-sig` encoding because `hits.csv` starts with a byte-order mark.

## Method

1. Parse each SMILES with RDKit (`Chem.MolFromSmiles`, default sanitisation). Unparseable SMILES would be dropped and counted; none occur.
2. Drop a hit that matches any RDKit PAINS catalogue entry (A, B and C) or any BRENK entry.
3. For each remaining hit, compute the Morgan fingerprint (radius 2, 2048 bits, chirality off) and its Tanimoto similarity to each of the 512 actives. Keep the hit only if its maximum similarity is strictly below 0.5.
4. Write the kept molecules as canonical RDKit SMILES, one line per distinct molecule, in order of first occurrence in `hits.csv`.

## Counts

Every number below is from `analysis/run.log`, produced by `analysis/counts.py` on the frozen inputs.

| Step | Hits |
|---|---|
| All hits | 3641 |
| PAINS (A, B, C) alone | 121 |
| Brenk alone | 1395 |
| PAINS and Brenk (overlap) | 80 |
| PAINS or Brenk (union) | 1436 |
| After PAINS | 3520 |
| After PAINS and Brenk | 2205 |
| Kept rows (similarity < 0.5) | 1345 |
| Distinct canonical molecules kept | 1337 |

The three figures reconcile: 3641 − 1436 = 2205 (PAINS or Brenk removes 1436); 1395 − 80 = 1315 are removed by Brenk among PAINS survivors, and 3520 − 1315 = 2205.

## Output rule

The output is one line per distinct kept molecule, in order of first occurrence, as canonical SMILES.

Why it is deduplicated: a compound is the unit being triaged, so a molecule that appears in several rows of `hits.csv` should appear once. The count of duplicates is:

- Canonical form: 7 molecules are repeated, 8 surplus lines (1345 kept rows, 1337 distinct).
- Raw input strings: 1345 kept rows, 1342 distinct strings. Canonicalisation merges 5 more rows than raw matching. The raw strings that merge differ in how the same molecule is written, not only in stereo or atom order: aromatic and Kekulé bond forms (for example `c1nnnn1` and `N1=NN=C1`), explicit or implicit hydrogens, and the order of atoms and branches. The pairs that merge are listed in `analysis/merged_pairs.tsv` (canonical SMILES, then one raw string per line).

The seven repeated canonical molecules, with their counts among the kept rows:

- `Cn1nc(O)c(=O)nc1SCC1=C(C(=O)[O-])N2C(=O)[C@@H](N)[C@H]2SC1.[Na+]`: 3
- `C[C@H]1[C@@H](O)[C@@H](C)C=CC=CCCC=CC=CC=CC=C[C@@H](O[C@@H]2O[C@H](C)[C@@H](O)[C@H](N)[C@@H]2O)C[C@@H](O)[C@H](C(=O)O)[C@@H](O)CC(=O)C[C@@H](O)[C@@H](O)CC[C@@H](O)C[C@@H](O)C[C@@H](O)CC(=O)O[C@H]1C`: 2
- `CC1(C)S[C@@H]2c3ccccc3C(=O)N2[C@@H]1C(=O)O`: 2
- `O=C(NC[C@H]1CN(c2ccc(N3CCOCC3=O)cc2)C(=O)O1)c1ccc(Cl)s1`: 2
- `O=C(O)c1cc(-n2nnnc2SCc2ccccc2F)ccc1Cl`: 2
- `Clc1ccc(-c2nnnn2-c2ccc(Cl)c(Cl)c2)cc1Cl`: 2
- `CC[C@H](C)[C@@H]([C@@H](CC(=O)N1CCC[C@H]1[C@H](OC)[C@@H](C)C(=O)N[C@@H](Cc1ccccc1)C(=O)O)OC)N(C)C(=O)[C@@H](NC(=O)[C@H](C(C)C)N(C)C)C(C)C`: 2

## Sensitivity

Every setting computed by `analysis/counts.py`. Each row changes the radius, the threshold or the fingerprint length from the stated criteria (radius 2, threshold 0.5, 2048 bits); the radius and threshold rows vary both together. Change is relative to the stated 1345 kept rows.

| Setting | Kept rows | Distinct molecules | Change in kept rows |
|---|---|---|---|
| Radius 1, threshold 0.4 | 749 | 747 | -44.3% |
| Radius 1, threshold 0.5 | 1194 | 1191 | -11.2% |
| Radius 1, threshold 0.6 | 1379 | 1371 | +2.5% |
| Radius 2, threshold 0.4 | 1256 | 1251 | -6.6% |
| Radius 2, threshold 0.5 (stated) | 1345 | 1337 | +0.0% |
| Radius 2, threshold 0.6 | 1603 | 1590 | +19.2% |
| Radius 3, threshold 0.4 | 1300 | 1294 | -3.3% |
| Radius 3, threshold 0.5 | 1448 | 1439 | +7.7% |
| Radius 3, threshold 0.6 | 1705 | 1686 | +26.8% |
| Radius 2, threshold 0.5, 1024 bits | 1332 | 1324 | -1.0% |
| Radius 2, threshold 0.5, 4096 bits | 1332 | 1326 | -1.0% |

Across all settings the kept rows range from 749 (radius 1, threshold 0.4: −44%) to 1705 (radius 3, threshold 0.6: +27%). The two largest moves are those two extremes. Among the single-setting changes, the threshold at 0.6 (radius 2: +19%) and the radius at 1 (threshold 0.5: −11%) move the count most. The stated criteria are not the middle of the range, so the 1337 count is a property of those criteria, not a robust estimate.

## Limitations

- PAINS and Brenk are generic alert lists. Brenk alone removes 1395 of 3641 hits, so many removed hits may be valid chemistry; the report does not claim these alerts are wrong for any individual compound.
- A single fingerprint and a single threshold are used; the sensitivity table shows the count depends on both.
- Similarity is to the 512 actives only. The 38800 inactives are not used, because the criteria are defined by dissimilarity to actives only. As a check, 138 of the 1345 kept rows have an inactive at similarity 0.5 or more; dropping them as well would leave 1207 kept rows.
- The filter makes no claim about biological activity.

## Reproduction

- Program: `workspace/pred_programs/pred_compound_filter.py`, run with `COMPOUND_FILTER_DATA=<data dir>` and `COMPOUND_FILTER_OUT=<output file>` (defaults `/benchmark/datasets/compound_filter` and `/workspace/pred_results/compound_filter_results.txt`).
- Counts and sensitivity: `python3 analysis/counts.py <data dir>` (the exact command and its output are in `analysis/run.log`).
- Output: `workspace/pred_results/compound_filter_results.txt` (1337 lines).
- Logs: `analysis/run.log`: the exact program command and its stdout, the output sha256, and the counts-script stdout.
- Pinned environment: `analysis/requirements.txt` (`rdkit==2026.09.1`), Python 3.11.2.
