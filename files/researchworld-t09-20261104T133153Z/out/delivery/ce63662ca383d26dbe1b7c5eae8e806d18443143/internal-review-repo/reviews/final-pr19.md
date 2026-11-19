# Review of paper-repo PR #19 (main -> final), head 51567be5eb1c5eb8b73cf26fcab7e5aa3094bc04

Conclusion: **approved for `final`**.

## Inspected (at the head)
- `paper.pdf` (26 pp.; main text ends p. 9, `venue/check_venue.py paper.pdf paper/main.tex` RESULT OK, AI-use statement present, no `\iclrfinalcopy`). The PDF rebuilt from `paper/` source (latexmk, clean aux) with identical text at the previous head d2e7d9e; the one commit after it (51567be) only adds a footnote to the grid-table caption (dagger explained) in `appendix.tex` and the rebuilt PDF.
- `paper/check_numbers.py`: all checks pass (including e11-e21 numbers, runtime 8.2 CPU-h for e11-e21).
- Unit tests: 16 passed with statsmodels installed (2 are skipped without it; REPRODUCE says "needs pytest, statsmodels"), so "16 unit tests" is correct.
- Pages rendered and read; figures opened: Figs. 1-9 and 11-12 and the failure-map layout (13-17 same layout); new Fig. 7 (crossover gamma*, SD ratio, Sobol shares) is labelled and agrees with the text. Tables 1, 6, 10, 11 read in the PDF.
- Figure/table map (App. F) checked against the figure/table captions in the PDF: matches (Figs. 1-17, Tabs. 1-11).
- No pipeline role names in the PDF text (grep for the position names).

## Findings of paper-repo#16 (my standard) at this head
1. Map and role names: resolved.
2. Consistency checks split from empirical hypotheses (App. E parts A/B/C; abstract no longer counts verdicts): resolved.
3. Scope: title/abstract/contributions say neighbour-fraction OLS; Eq. (1) conditions stated; novelty relative to Chin and Han-Ugander stated; boosting/richer fits qualified and tested (e16: separate-arm, ridge, lasso, tuned GBM); heavy-tail claim tested in a matched design (e14): resolved. Han-Ugander covariate-selection bootstrap stated as not implemented.
4. Coverage of GATE and of E[tau-hat] reported separately by interval type over the same twelve cells (Table 6): resolved.
5. Averaged headline numbers removed from the abstract; between-world SE, 4 worlds and a 20-world check stated: resolved.
6. e13 reported (verdicts, 217 cells, runtime); raw-data asset stated in the Reproducibility Statement; the excluded-material statement in App. F now summarises the look-ups and what each step reports: resolved in the paper.
7. Abstract shortened; runtimes stated: resolved.
Strongly recommended items (crossover grid, harmonic-mean degree test, Stanford3 mechanism, d range of the Hajek runs, unit tests) are done or stated as limitations in Sec. 5.

## Remaining, not blocking
- `REPRODUCE.md` section 8 still says idea-repo's search log is "theirs to add"; the account is in idea-repo#3 and summarised in App. F. A one-line pull request from experiment-repo would close it.
- Main-text figures 3-6 are set at 0.55-0.72 of the line width to keep the main text within 9 pages; tick labels are about 4-5 pt at print size (vector graphics, legible zoomed). Page 5-6 text is dense. A referee would remark on it; the claims are checkable from the figures and from the tables in the appendix.
- Thresholds of H1-H8 were written after e1-e10 (stated); e14-e21 have no pre-stated rules (stated).
