# Result-to-artifact plan

Prepared against experiment-repo e489570fe452dcb8191cf768aa0c2be6202e2b36 and its analysis/methods.md. Numeric summaries are still pending; no figure has been rendered from unfinished runs. code/render.py is ready to consume the specified summary.csv, paired.csv, and theory.csv. It has passed Python compilation only; numerical validation, venue sizing, and visual inspection remain owed.

The candidate outputs, to be adjusted to the story and venue decisions, are:

- synthetic.pdf: paired coverage and width columns; rows quadratic, sigmoid, linear, null. Methods PPI++, unclipped scalar, cross-fit linear, cross-fit cubic. This exposes nonlinear gain and controls without selecting scenarios for favorable outcomes.
- stress.pdf: heavy-tailed, quadratic Bernoulli, rare Bernoulli rows; includes degree-12 cross-fitting to expose nuisance estimation limitations. Axes expand to show all coverage intervals.
- real.pdf: galaxies, forest, alphafold rows; label-only/PPI++/unclipped scalar/cubic. The empirical archived-record sampling population must be explicit in the caption.
- finite.pdf: bounded-quadratic supplement, comparing EB label, full-label EB PPI, EB scalar, EB cubic. These theorem-backed intervals are shown separately from Wald intervals.
- main_results.tex: all ten main regimes at n=2000, PPI++ and cubic coverage/absolute widths and paired mean-width ratio.
- finite_results.tex: bounded-quadratic EB absolute widths, coverage, and ratios against EB label.
- binary_results.tex: exact Clopper--Pearson and all-label EB label/PPI plus trained scalar/cubic EB comparisons on all five binary main regimes at n=2000, plus rare Bernoulli at n=100. Explicitly retain the exact baseline rather than comparing only against conservative EB.
- oracle_ratios.tex: exact leading-order oracle/scalar and oracle/label ratios from the analysis owner's theory.csv, distinctly labeled analytical predictions, not measured performance.
- all_cells.csv and all_paired.csv: unfiltered summaries to make omissions visible. A manifest records input checksums, analysis revision, and rendering versions.

Common caption requirements: N=10n, independent repeated draws, same inputs across methods within each draw; 95% target; two-sided 95% Wilson intervals for empirical coverage; ratio of paired mean widths, with delta-method Monte Carlo intervals; sample size and repetitions; varying vertical scales across regimes if retained. Horizontal point offsets are display-only. A Monte Carlo interval crossing .95 does not prove validity, and narrower Wald intervals with poor coverage are not declared improvements.

Main results use 5000 repetitions per cell, bounded supplement 3000, subject to final completion metadata. Absolute width is in the outcome's units; widths across different regimes are not directly comparable. Known-truth synthetic and empirical-population archived-data evidence must be distinguished from field-level scientific inference. A final delivery will include complete captions, and every figure/table will be opened at the selected venue's final size before handoff.

## Settled path/layout update

Story-repo #3 is answered: figures/, tables/, presentation/ are assigned to figtab-repo by paper-repo CODEOWNERS. NeurIPS 2026 text width is 5.5 inches, single column. Generator moved to presentation/render.py and default width is 5.5. A full longtable will preserve every summary cell as readable appendix material in addition to CSV exports. Brief was read in full on 2026-11-02; its paired validity/width conventions and scope restrictions are reflected here.

The oracle table has now been generated from the committed actual theory.csv, compiled in the official venue style, and opened for visual inspection. The first render caught pandas interpreting the scenario string `null` as missing; all CSV loads now preserve scenario text explicitly. Empirical outputs remain pending, with no placeholder figures. The n=N follow-up is analysis-owned; its final supply must be accommodated without treating it as part of the N=10n original grid.

## Measured delivery completed

Committed numeric summaries are now supplied at experiment-repo 317d3f6eb010c335540a0d685581f17554fa812e. Final selections and captions are in presentation/captions.md. The two main figures combine prespecified benefit/no-gain/archive/failure cases and separately compare theorem-backed EB/CP. Full output includes seven figures and seven table files; full_results.tex retains all 405 method/setting rows with n,N,R, coverage uncertainty and width MCSE, including n=N follow-up and every diagnostic. Source snapshots and a bit-identical deterministic rerender were checked. All figures and 12 compiled-table pages were opened; fonts, widths and table bounds passed. This meets the numeric presentation commitment pending integrated-paper inspection after merge.
