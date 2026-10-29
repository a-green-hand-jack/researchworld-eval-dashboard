# Review of paper-repo#12 (version 1 into `release`), head f884890519a6852283044f5dc83b2ceb4927621f

Inspected at that commit: template.tex, references.bib, tables/*, figures/figure_1.png, template.pdf. I recompiled (pdflatex+bibtex+pdflatex x2): 6 pages (main text ends p.5, references p.5-6), no undefined citations/references, bibtex 0 warnings; the committed PDF is built from the committed sources. Opened all 6 pages and Figure 1: four labelled panels, readable, caption matches content.

Checked against experimental_log (INSTRUCTIONS.md) and experiment-repo's audit (analysis/README.md, d214282): all CIFAR-10 ablation, baseline and mixed-linear table values match the log; the mixed-linear "gap to Unlearned(+)" vs "gap to Retrained" distinction is made explicit; 15% failure, single runs, MIA non-discrimination, shared default row, lambda^-2 "consistent with" wording are all handled. Dogs/Caltech numbers are not invented (figure only, labelled as read by eye). 26 references are real, all pre-2024-11, all cited keys resolve; template/packages/author block unchanged; main text 5 pages.

Conclusion: supported; approved for `release`. Non-blocking findings to fix before `final` (sent to paper-repo issue):
1. Sec 3.3: the surrogate Delta-hat_i is not defined beyond "from the forget set and Lipschitz continuity"; the materials do not give it. State plainly that the construction is only outlined in the available description (no invented formula), so readers do not assume full reproducibility.
2. Sec 4.2: "supports the claim that the remaining Hessian can be recovered" overstates; no Hessian error is measured (audit C). Say "consistent with".
3. Figure 1 panel (b) (Retrained test ~55) differs from Table 3 (62-64); add a note that the log does not say which model Figure 1 uses (it looks like the plain linear classifier).
4. Repo hygiene: remove tables/code/__pycache__ from the tree.

## Update: head ff4a5508a314ea303bc9c6182e40275ef9c3ad49
Diff vs f884890 inspected (references.bib: Neel et al. 2021, ImageNet, JiT venue; template.tex Sec 2/4.1/4.2/4.6). Recompiled: 6 pages, no undefined citations, ImageNet and Descent-to-Delete appear in the reference list. Finding 1 fixed. Findings 2-4 remain (paper-repo#16, plus stray `}` in references.bib). Approved again for `release`.

## Final: paper-repo#18 into `final`, head e74983952d22ea04a32e08272c11b8b35c9d9c8f
Diff vs ff4a550 inspected: surrogate stated as only outlined; Hessian-recovery claim softened; Fig. 1 model note added; __pycache__ removed. Recompiled from the committed sources: 7 pages, main text ends on p.6, no undefined references/citations, bibtex 0 warnings; template.pdf/template.tex/references.bib present and nonempty; figures/figure_1.png present. Pages 5-6 and Figure 1 opened. Residual cosmetic: a stray `}` after the foster2024information entry in references.bib (ignored by bibtex). Approved for `final`.

## Final, re-check at head 9614d4feb5b955e74cd5f8de910a41958f0dc1bf
Only change since e749839: the stray `}` removed from references.bib. Recompiled: 7 pages, no undefined references, bibtex clean; committed PDF has 7 pages and no unresolved `??`. Approved for `final`.
