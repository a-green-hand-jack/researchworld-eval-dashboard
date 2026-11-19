# Review of paper-repo PR #9 (final-proposal -> final), head 59da74c60634428eb7df305f3f18ac7672e9fe2d

## Inspected
- Compiled `paper/main.pdf` (20 pp, main text ≤ 9 pp, checklist after references) and all 8 figures + 9 tables rendered and opened: none blank, labelled, readable (Fig. 1/4 and Table 3 use small fonts but are legible). Forced rebuild of `paper/` from source (`latexmk -g`): 0 undefined references/citations, text identical to the delivered PDF.
- `venue/check_venue.py` passes all items.
- Numbers spot-checked against `code/results/*.csv`: 24/26 M4-wider cells and ratio ranges per n; M3 coverage at n=50 (0.904/0.838/0.923/0.925); census-income M3 coverage series; classical/M3 width 1.18–3.70, M2/M3 0.987–1.025; plankton coverage series (M4 0.90/0.80/0.67/0.49/0.18; M3/M2/jk 0.94–0.97; control 0.93–0.94); Table 8/9 entries. All agree.
- Independent re-run: `tests/test_jackknife.py` passes; forest n=100, N=2000, R=2000, final seed space re-simulated from the delivered code and public data (ppi-python 0.2.3): M3 coverage 0.924 / width 0.1187, M4 0.9215 / 0.1236, classical 0.932 / 0.1403, paired M4/M3 1.0414 — identical to `summary_final_real_primary.csv`.
- Honesty: null result on real data, conditional gain on synthetic data, small-n undercoverage and shift failure reported as such; post-hoc spline ablation labelled post-hoc; untested explanations flagged as untested; conformal baseline absence explained; forbidden-content log present with idea-repo's disclosure; citations are the starter list plus classical references.

## Conclusion
Supported: the question (can the fixed-input interval be shorter, by how much, when) is answered conditionally with an efficiency ceiling, paired-width/coverage evidence with MC uncertainty on nine real datasets and 45 synthetic cells, and honest limitations. Approve.

## Non-blocking nits (not requiring a new head)
- Sect. 5.1 says M2 is "within ±2.5% of M3 everywhere": the data give 0.987–1.025 in the primary cells (appendix cells not rechecked); fine, but "about 2.5%" would be safer.
- Estimand is only the mean; quantiles/regression and use of X are declared out of scope (stated in limitations).
