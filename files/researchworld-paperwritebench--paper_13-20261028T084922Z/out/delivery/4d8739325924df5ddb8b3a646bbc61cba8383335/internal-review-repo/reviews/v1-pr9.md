# Review of paper-repo PR #9 (Version 1 into release), head 1b55426278e84a2a5c057ac37a5635b0fe2e0dad

Inspected at that commit: template.tex, references.bib (byte-identical to supplied), tables/*.tex, all eight figures (opened and viewed), code/figtab.

Verified
- All \cite keys exist in references.bib; no filecontents; \graphicspath kept; no Acknowledgements section; every figure/table file referenced exists and renders (stub-class build: 0 errors, 0 undefined refs/citations).
- Counts and derived numbers (60.4% / 23.4% / 3.7% survival, 13.5 images/user, 2.07 boxes/image, 65.8 boxes/class, 61.6% / 15.8% in step 3, class change -962 = 1180-218) recompute from table_zn and the overview.
- Task 1 text vs table_kf: ranks, R@5-R@1 gaps, F1/R@1 ratios, Spearman 0.53 / 0.94 recomputed and correct.
- Task 2 readings checked against both plots (zero-shot ~0.23 -> ~0.16, min ~0.09; LoRA ~0.26 -> ~0.49; full ~0.24 -> ~0.51; User A: zero-shot 0.05-0.14, all-user 0.30 -> 0.65, user-only 0.17 -> peak ~0.67 -> 0.57, ahead Aug-Nov). Honest; differs from the overview's "~20% to >50%" rounding but follows the figure. Histogram readings (16 classes at floor, largest ~1.7e3) match.
- Task 3 numbers match table_vs; 687/1,222 (net 535) come from the overview; the table_vs vs table_kf identical-row inconsistency is disclosed.
- Benchmark-paper framing, validation section, discussion of limits: conform to AGENTS.md.

Not verifiable here
- acmart is not installed and could not be fetched; build was with an article two-column stub (10 pt): body about 8 pages + 2 pages of references. A real sigconf 9 pt build is unverified.

Open findings (request changes)
1. Length: objective asks for a 6-page double-column paper; PR text itself estimates ~6.4 body pages + references, and my stub shows more. Trim so the body is within 6 pages in real acmart, or show a real build.
2. Typo in Section 3.2: ``Milk or a product label labeled ``Donut) - unmatched quotation marks (missing closing '' and paren).
3. "by construction no class has fewer than 10 images": the <10 filter is step 3, before outlier removal/manual review/merge, so it holds only for the histogram as plotted (x-axis starts at 10). Reword.
