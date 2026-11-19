# Review of paper-repo PR #9, round 2
Head inspected: 508e5873d73167368372e1f36e1c6fd0b57b2697 (paper.pdf 23 pages; check_format PASS, main text 9/9 pages).

## Round-1 findings, status at this head
- F1 attribution (correction, not stratification): resolved. Abstract, Sec. 5.2, Sec. 6, new Table 3 (ablation with two-level bootstrap). I recomputed: extrap n=50 random+lowrank_dr -0.99, strat+lowrank_dr -1.10, strat+lowrank +3.54, strat+mean -0.77 vs B1 from tier1.parquet; match.
- F2 abstract overstatement: resolved (anchor points / B2 listed separately).
- F3 target-model uncertainty: resolved. Two-level bootstrap in Table 3/6, statement of what the bands cover. I verified from results/tables/review/target_bootstrap_by_benchmark.csv (baseline random+mean): no cell with an interval above zero for B2, P3 DR, P3 EB, random+lowrank_dr (0/78 each); P3 DR benchmarks below zero extrap 11/13/10 (n=20/50/100), random 12/13/13; P3 EB extrap n=50 6/13: all match the text.
- F4 RMSE/Kendall: resolved (Table 6, appendix tables).
- F5, F6, F7 (survey-sampling/PPI/IRT citations, P3 not claimed novel), F10 (abstract-level statement): resolved.
- F8 Fig. 2 legibility: resolved (Fig. 1 full-width macro figure, legible). F9 pycache: resolved. Tier-2/3 analyses are now in (organisation hold-out, factorial, source-set size, rank ablation, coverage), with their subset sizes disclosed.

## New findings at this head
N1 (blocking) Table 2, the headline macro table of the main text (p. 5), renders with "--" in every cell. paper/generated/tab_macro.tex is all dashes. Cause: paper/make_tables.py `macro()` selects rows with `benchmark.isna()` from figures/generated/fig_{mae,spearman}_vs_n_{split}.csv, but the regenerated per-split CSVs no longer contain macro rows (the macro curves moved to fig_macro_curves.csv, columns method,n,mean,lo,hi,nbench,split_type,metric). The PDF was built from the broken table. Fix make_tables.py (and make it fail loudly instead of printing "--" when a required cell is missing), rebuild, and check every generated table for dashes other than the intended ones (B0 Spearman; Table 6 Kendall; Table 8 combinations not run). The text quotes values from this table (4.60 +-0.13 etc.), so the numbers must be visible.
N2 Checklist item 1 (Claims) justification is stale: it still says "stratification with a correction is the robust option with a small edge", which the paper now refutes. Update it to the new finding; re-read the other 15 justifications against the new text (items on statistical significance and limitations were updated; item 1 was not).
N3 Table 5 caption still says the squared bias "is estimated from 30 draws"; Sec. 5.4 now says ~7.5 draws on the random split. Make the caption say per split.
N4 Format WARNs: Type 3 fonts persist on pages 1,3,4,5,6 (same pages as before the figure change, so not the figure PDFs: check pdffonts on paper.pdf and find the source, e.g. the tiny table fonts or tikz/ps fonts); the checklist spans 10 pages because the template's guideline text was left in (the NeurIPS instructions say to delete the guidelines); remove them. The appendix has empty run-in headings "All four metrics." and "Tables of the further analyses." with no text; give them text or remove them.

## Conclusion
Everything checked numerically against the delivered tables holds, and the claims are now supported with the right uncertainty. The version cannot be approved with the headline Table 2 blank (N1); N2-N4 should be fixed in the same push. Changes requested.
