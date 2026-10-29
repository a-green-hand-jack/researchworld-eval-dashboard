# Feasibility note: compound filter study

Owner: idea-review-repo (feasibility). Scope: judgement only; this note produces no filter results.

## Settled inputs (story-repo#6)
- Fingerprint: RDKit Morgan, radius 2, 2048-bit bit vectors; keep if max Tanimoto to actives is strictly below 0.5.
- Actives: `ACTIVITY == 1` rows of `train.csv` (512 rows, measured).
- Exclusion: any PAINS (A, B, C) or BRENK match via RDKit FilterCatalog.
- Output: surviving SMILES, one per line, in `hits.csv` order, to `workspace/pred_results/compound_filter_results.txt`; invalid SMILES counted and dropped.

## Measured facts
- `hits.csv`: 3,641 data rows; 0 invalid SMILES under RDKit; header carries a UTF-8 BOM (read with `utf-8-sig`).
- `train.csv`: 39,312 data rows, all 2-column; 512 actives, 38,799 inactives.
- RDKit 2026.09.1 installed in `/hutian/.venv` via pip (not in the sandbox image).
- Dry run (diagnostic, not a deliverable, same settings as above): 11.0 s wall time on 2 CPUs; 3,641 hits, 0 invalid, 1,345 kept. The kept count is a diagnostic and is not evidence of correctness; experiment-repo owns the analysis.

## Judgement
- Feasible at low cost. Compute is seconds, so no background job is needed.
- Risks: (1) SMILES in the hits file are not canonicalised and may differ from train; this affects only the similarity values through the fingerprint, not feasibility. (2) The Brenk catalogue version affects the exclusion count; record the RDKit version used.
- Scope limits: none beyond the settled choices. No demonstration substitution is proposed.
- Bounds to record in the delivery: pin RDKit version; state the 0.5 threshold is strict.
