# Review of paper-repo PR #6 (main -> release), head c405f94ce9bee63099b1f72dbe96c27e2069e829

Inspected: workspace/pred_programs/pred_compound_filter.py and workspace/pred_results/compound_filter_results.txt at that commit.
- Re-ran the program (RDKit 2026.09.1) on the frozen inputs: 3641 hits, 0 invalid, 1436 PAINS/Brenk, 860 similar, 1345 kept; output byte-identical to the delivered file.
- Independent re-implementation (csv + rdFingerprintGenerator Morgan r2/2048, PAINS_A/B/C + BRENK catalogs, 512 actives with ACTIVITY==1, strict < 0.5): kept list identical, same order.
- 6 hits sit at exactly 0.5 and are correctly excluded (strict "<0.5"). 1345 lines contain 1342 distinct SMILES (duplicates exist in hits.csv; harmless).
- Output: original input SMILES, one per line, no header.
Conclusion: meets the commitment in #2. Approved.
