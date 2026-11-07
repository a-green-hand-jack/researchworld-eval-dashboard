# Review record: paper-repo#16 (final), head 8ac28ac

Earlier approval was at 6de34f1 (reviews/paper-pr16-6de34f1.md). The head moved to 8ac28ac (figures/tables of figtab-repo#15/#17/#18 merged, paper/main.tex now includes them), so the approval was withdrawn and this head was reviewed.

## Inspected
- `git diff 6de34f1 8ac28ac`: README artifact map, paper/main.tex (Fig. 3b reference, Appendix Table 8 path, Fig. 5 window sweep now present), figures (fig4 panel b, fig6, fig8_window new), tables (table0 iid/cluster z, table5 random-removal columns, table4 ablation rows, table6b estimator new, table7_oos, table8_restarts), tables/MANIFEST.json.
- Regenerated all figures and tables in a scratch copy (`make_all.py` with absolute paths, `quoted_numbers.py`): no .tex table and no quoted_numbers.tex changed (PDFs differ only in embedded metadata).
- Rebuilt paper/main.pdf: 20 pages, no undefined references, venue checker OK (9 main pages, 16/16 checklist answers); text identical to the committed PDF; no PENDING/?? markers.
- Viewed pages 6, 7, 10: Fig. 3a/b (budget vs z; first-order estimate vs verified budget, "99.9% of 1419 claims within 2x"), Table 3 (new random-removal columns), Fig. 5 (window sweep, values 21/7/4/2/4 and 3 constant match the text), Fig. 6 (noise-equivalent budget). All legible, labelled, consistent with the text.
- Spot-check of Table 3 against results/s5_noise.csv: Arena 1245, GPT-4 2111, NBA all 946 reproduce.

## Findings (not blocking)
1. MT-Bench human noise-equivalent budget: text (Sec. 4, "2833 on MT-Bench human") takes the median over the 4 claims where a flip is reached; Table 3 reports 2888 because it counts the one "never" claim as infinity. Both are defensible, but text and table should use the same convention. Also the Fig. 3 link "3a" collides with its box (cosmetic).
2. Table 7 NBA row label "(7 sampled)" still confusing (carried over from the previous review).
3. Residual limitation, disclosed in the paper: no lower bound for the large-instance budgets (exhaustive search only on 6-model subsamples plus randomised restarts); the budgets are verified upper bounds.

## Conclusion
All objective requirements and my earlier findings (F1-F6) remain addressed; the new figures/tables regenerate from results/ and match the text. Approve.
