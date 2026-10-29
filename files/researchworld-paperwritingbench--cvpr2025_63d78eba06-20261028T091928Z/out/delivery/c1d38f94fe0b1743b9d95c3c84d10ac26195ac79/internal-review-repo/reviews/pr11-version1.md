# Review of paper-repo PR #11 (Version 1, into `release`)

Head inspected: 9de96174f706cb0601aac73def88c77cd9c45225. Status `hutian/delivery`: success.

## What I inspected
- `template.tex`, `references.bib`, `template.pdf`, `figures/`, `tables/` at that commit. The template header, `cvpr.sty`, `ieeenat_fullname.bst`, `preamble.tex` and `figure_1.png` are byte-identical to the supplied inputs, apart from the title. The author block is the required placeholder.
- Recompiled from source (pdflatex, bibtex, pdflatex x2): no undefined references or citations, no overfull boxes, 7 pages with references. The text of my build is identical to the delivered PDF (differences are only back-reference page numbers from the extra hyperref pass).
- All 7 pages rendered and viewed. Main text ends on page 5 (about 5.3 pages), well under the 8-page limit.
- Every number in Tables 1 to 3 and in the text against the experimental log in INSTRUCTIONS.md: baseline table, forget-size, perturbation and lambda tables, mixed-linear table. All match. The |Delta| rows in the mixed-linear table are recomputed correctly (vs Retrained and vs Unlearned(+)).
- Figure 1 (`figure_1.png`, opened): the paper's read-off values match the bars to about 1 point, and are marked approximate. Figure 2 (`fig_ablations.pdf`, opened at 130 dpi): legible, labeled axes, four metrics distinguished by marker and line style as well as color, and the plotted points match the log (e.g. perturbation 250: 15/16/15, MIA 6.2).
- Bibliography: 27 entries, all cited keys exist, no unused keys, all dated 2024 or earlier. I spot-checked eight entries against Crossref (titles, pages, venues, authors) and found no mismatch. arXiv:2402.01401 is JiT as stated.

## Conclusion
The version is supported. It does what the critical constraints require: numbers are copied from the log, the single-run limitation is stated, the log's inconsistencies (differing Retrained rows, mixed-linear gaps relative to Unlearned(+), remaining accuracy above Retrained, the repeated default row) are disclosed, "comparable to retraining" is scoped to CIFAR-10, the 1/lambda^2 bound is not claimed, and no theory is invented. The 15% and 250-perturbation failures are reported as limits. Approved.

## Non-blocking nits (sent to paper-repo as an issue; address in a later version if there is one)
1. Section 4.2: "MIA stays within about 1.5 points of 50% for all models and datasets" disagrees with the figure's own caption (~50 to 52) and with the CIFAR-100 bars (~52); say "about 2 points".
2. Retrained rows "are separate runs for each forget set" is an inference, not in the log; reword as "differ across tables; the log does not say why".
3. The binomial standard-error estimate assumes test-set sizes (10k, 2.5k) that are not in the log; present as illustrative.
4. Method: Eq. (3) (the penalty rho, the quadratic model q, the estimates Delta_k) goes beyond idea.md. The paper states that these details are not in the logs, which is acceptable, but "Lipschitz continuous in the sense used by the estimator" is vague; consider removing it.
5. The main text uses about 5.3 of 8 pages. Nothing in the supplied material calls for more content, and I would not add anything not backed by it.

## Addendum: head moved to 11a0fbe6d458435e9750c5e9164af8a3e4dfa9c6 (merges of paper-repo PRs #12 and #14)
I reviewed the diff from 9de9617 (`template.tex` and the rebuilt `template.pdf` only). It fixes nit 1 (MIA "within about 2 points") and adds that Unlearned(+) shows the same shortfall against Retrained (~4.8 vs ~3.9 points on average, from bars). I recomputed these from the figure and they hold. It also rewords the ablation table pointer. Recompiled from source: 0 undefined or overfull warnings, 7 pages, text identical to the delivered PDF. The approval is on 11a0fbe. Nits 2 to 4 remain open and non-blocking.

## Addendum 2: head moved to 3f0063b5a2d5ff7fa9db6182b767b4a5e6600234 (paper-repo PR #16, wording for nits 2 to 4)
Diff from 11a0fbe is `template.tex` wording (the unlogged explanation is hedged, the test-set sizes are marked illustrative, the smoothness wording is simplified) and the rebuilt PDF. No number, table, figure or citation changed. Recompiled: 0 undefined or overfull warnings, 7 pages, text matches the delivered PDF. All nits are closed. Approval re-issued on 3f0063b.

## Final (paper-repo PR #17, into `final`)
Head 3f0063b5a2d5ff7fa9db6182b767b4a5e6600234, the same commit I inspected and approved for PR #11 (merged into `release`). Status `hutian/delivery`: success. Nothing changed since the inspection above, so the conclusion stands: supported. Approved.
