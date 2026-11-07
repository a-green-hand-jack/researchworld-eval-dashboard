# Restricted reading record

Access date: 2026-11-02. Only direct PDF URLs from the explicitly permitted starter
list were used. No search engine, thematic literature query, citation graph,
paper aggregator, author page, repository search, or related-paper link was used.
Downloaded versions are identified by their first-page arXiv markers. Reading
was focused on the sections below, not a claim to have reviewed every proof or
reference in each document. Local SHA256 hashes and source URLs are in
`provenance.json`. No prohibited source was encountered. The prohibited work's
identity was not inferred or investigated.

1. **Angelopoulos and Bates, 2107.07511, version 6 (7 Dec 2022).**
   Direct URL: https://arxiv.org/pdf/2107.07511 . Read opening framework and rank
   construction, Section 2.3 score normalization, Sections 3/3.1 evaluation and
   conditional coverage, and Section 4.1 group-balanced calibration. Used to
   establish that marginal coverage, adaptivity checks, and group calibration are
   established practice. No novelty is claimed for these general principles.

2. **Lei et al., 1604.04173, version 2 (8 Mar 2017).**
   Direct URL: https://arxiv.org/pdf/1604.04173 . Read abstract, introduction,
   Section 2 split/full distinction, Theorem 2.2 and nearby split-conformal
   discussion, and the description of locally varying intervals. Used for the
   fixed-score split guarantee and scope relative to data-reuse procedures.

3. **Tibshirani et al., 1904.06019, version 3 (6 Jul 2020).**
   Direct URL: https://arxiv.org/pdf/1904.06019 . Read abstract, quantile lemma,
   covariate-shift model, Corollary 1, and Section 2.2 weighted split conformal.
   Important implementation detail: normalized calibration weights are combined
   with the test point's weight at infinity. We implement known density ratios,
   not estimated weights or robustness to arbitrary shift.

4. **Angelopoulos et al., 2009.14193, version 5 (3 Sep 2022).**
   Direct URL: https://arxiv.org/pdf/2009.14193 . Read abstract, introduction,
   class-label coverage event, and APS/RAPS motivation and algorithm overview.
   Used only to distinguish discrete label sets from regions for probability-valued
   responses. We do not rerun or claim numerical comparisons to RAPS.

5. **Javanmardi et al., 2402.10723, version 1 (16 Feb 2024).**
   Direct URL: https://arxiv.org/pdf/2402.10723 . Read abstract, introduction,
   response-space setup, Sections 3/4 distance and Dirichlet likelihood scores,
   Theorem 4.1, noisy-label assumptions in Section 4.1, and the opening discussion
   of inefficiency in Section 5. Used to position simplex conformalization,
   probability-valued targets, distance scores, and density scores as prior work.
   We do not claim novelty for any of those constructions or transfer their
   empirical results to our own study.

Conference formatting sources (not scholarly content searches): official NeurIPS
2026 call for papers and linked formatting ZIP, official NeurIPS ethics guidelines,
and ICML 2026 author instructions while choosing a conference. NeurIPS instructions
state nine main-content pages; references, checklist, and appendices do not count.
The official 2026 checklist has 16 items; all questions and guidelines are retained.
The attempted `/2026/PaperInformation/StyleFiles` path returned 404 and was not
used. The current-year style ZIP linked by the call for papers was successful.
