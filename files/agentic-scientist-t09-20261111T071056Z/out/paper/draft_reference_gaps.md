# Draft Reference Gap Memo

**Status:** ready — three targeted retrieval needs.

Existing coverage is adequate for design-based estimation (Aronow, Ugander, HT variants), GATE designs, and regression-based GATE estimation (Chin, Han and Ugander). Quantitative claims are grounded in `paper_data.json` and are not flagged. The gaps below are the places where positioning or background statements are thinly supported.

## Missing literatures
- Exposure-mapping misspecification and unknown interference
- Foundational interference/spillover and bias of naive estimators
- Variance and confidence-interval estimation under network dependence

## Targets

1. **thesis-exposure-mapping-misspecification** (introduction, priority HIGH, positioning)
   The central thesis is that fidelity of the fitted exposure mapping governs accuracy. The corner-extrapolation account in Results supports it. Only Aronow2013EstimatingAC is cited for "exposure mapping", and nothing covers misspecified mappings, unknown interference, or extrapolation to the all-treated/all-control corners (overlap/positivity). Reviewers would expect the paper to position itself against that work.
   - Anchor: "accuracy is governed by the fidelity of the fitted exposure mapping to the generating mechanism"
   - Search topics: misspecified exposure mapping bias under network interference; average treatment effects under unknown interference; positivity/overlap extrapolation for global effects.

2. **intro-interference-dim-bias** (introduction, priority MEDIUM, background)
   The first paragraph states that network A/B tests violate no-interference and that DiM is systematically biased for the GATE. These are uncited foundational claims; only HT estimators are cited there.
   - Anchor: "The difference-in-means (DiM) estimator, which is unbiased without interference, is systematically biased..."
   - Search topics: causal inference with interference/spillovers; bias of difference-in-means in network A/B tests.

3. **reliability-interval-undercoverage** (results, reliability subsection, priority MEDIUM, comparator)
   Coverage of 0.839 against a nominal 0.95 is a headline negative result. The draft explains that HC1 intervals ignore cluster dependence and use no resampling, but it cites no work on variance estimation or confidence intervals under network dependence.
   - Anchor: "ignores cluster dependence under the cluster design and uses no resampling"
   - Search topics: variance estimation under network dependence in interference experiments; cluster-robust or network HAC standard errors.

## Not flagged
The related-work paragraphs on design-based estimation, designs, and regression adjustment are densely cited. The HT, graph-cluster-randomization, and Chin/Han comparators are covered. GNN/Facebook100 mentions appear only in limitations as untested extensions and need no added support.
