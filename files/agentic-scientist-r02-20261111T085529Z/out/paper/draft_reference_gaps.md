# Draft reference gap memo

**Status:** ready (3 targets). No retrieval was run in this stage.

## Summary
Related work cites many peripheral conformal papers (class-conditional, efficiency, time series, clinical applications). It does not cite the foundational and directly-used sources: the baseline score functions, split/Mondrian conformal, and weighted conformal under covariate shift. `references.bib` contains no Vovk, Romano, Angelopoulos, Tibshirani (weighted) or Aitchison entries. The appendix already acknowledges that these are "stated as background without citation".

## Missing literatures
- Split (inductive) and Mondrian conformal prediction foundations
- Weighted conformal prediction under covariate shift
- Conformal classification scores (LAC, APS, RAPS)
- Compositional data analysis (Aitchison log-ratio geometry)

## Targets

1. **baseline-score-sources** (high, comparator) — Method, "Baselines, negative controls and validity conditions". The headline claim is a margin over the best of LAC/APS/RAPS/class-wise LAC, yet none of these is cited. Search: LAC / least-ambiguous set classifiers; APS; RAPS; class-wise split conformal.
2. **mondrian-split-conformal-foundations** (high, background) — Method, "Statistical background". The Proposition and rank argument are called textbook but unsourced, and Mondrian calibration is the core of the method. Search: Mondrian conformal prediction (Vovk et al.); split/inductive conformal; distribution-free finite-sample coverage.
3. **weighted-conformal-shift-and-compositional-framing** (medium, positioning) — Method, "Weighted calibration under covariate shift", and Related Work, "Positioning". The gated weighting step and the shift axis lack their source (weighted conformal under covariate shift; classifier-based density ratios). The log-ratio compositional framing is uncited. Search: conformal under covariate shift; probabilistic-classifier density-ratio estimation; Aitchison compositional data.

## Deliberately ignored
- Quantitative results (grounded in `paper_data.json`).
- Further applied or tutorial conformal papers, and the existing Related Work paragraphs on other output types.
- Real-data or CIFAR-10 literature, which would require reshaping the paper's synthetic-only scope.
