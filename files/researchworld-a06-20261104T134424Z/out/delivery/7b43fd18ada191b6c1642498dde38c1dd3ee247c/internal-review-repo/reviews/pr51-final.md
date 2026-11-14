# Review record: final version (paper-repo#51), head fa1e122ffcf714de1167b889a8268032ade8bad1

Conclusion: approved.

## Inspected
- `hutian/delivery` status on the head: success.
- `python3 -I paper/quote_numbers.py` regenerates `paper/` with no diff; a fresh latexmk build matches `paper.pdf` (26 pages); no `.pyc` tracked.
- Abstract and Sec. 4.2 numbers checked against `results/real_summary.csv`, `real_gaussian_max_check.csv`, `compute_log.json`, `generator_calibration.csv`: matrix 60x2000, accuracy 15.2-20.8%, 120,000 forward passes; naive gap 9.3/6.4/4.2/2.8 pp at n=50/100/200/400; naive coverage 0.709 at n=200 (0.641 at n=50); false-claim 25% (n=200) and 27% (n=50); SH, SR, greedy gaps; Gaussian-max check (63 cells, max 0.36 pp, 6 cells beyond 2 s.e.).
- Table 3 (real, n=50 and 200, all methods) matches the csv cell by cell; Table 4 (equal total items) supports the quoted RMSEs (2.7 oob, 3.4 and 3.8 fresh 50/150 and 100/100, 3.9 split, 5.1 naive); synthetic Tables 1-2 support the discussion numbers (4.5 vs 2.8 pp; hybrid 5.6 vs naive 5.2).
- Opened at reading resolution: Fig. 4 (three panels, labelled axes, legend, MC error bars, Gaussian-max lines), Tables 3, 4, 7, 8, 9. No blank, placeholder or unreadable exhibit. Table 8 values agree with the text (+6.8% / -1.3% mean, 31 and 4 of 63 cells beyond 2 s.e.).
- Scope statements: not-run items (real leakage arm, real two-system comparison, per-subject analysis, DSPy/MIPRO, large K, stronger model) are stated in the abstract/limitations and not claimed anywhere. No K=21 / interim / pending wording remains in the paper; run-time rows in `code/README.md` keep their K=21 timings as records.
- Earlier findings (stale hybrid row, K=60 scale, estimands, definitions) are resolved at this head.

## Non-blocking remarks
1. Checklist item 2 justification still says "the reduced K"; the study now has all 60 planned configurations. Wording only.
2. Sec. 4.2 says the matched generators reproduce the real gap "to within about ten percent"; Table 8 shows one-rho copula range -10 to +16% and 31 of 63 cells beyond 2 s.e. (the text and Appendix E do disclose both). Wording only.
