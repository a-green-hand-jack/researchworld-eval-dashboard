# Post-Draft Reference Query Plan

**Status:** ready. Four queries, one or two per gap target in `draft_reference_gaps.json`.

**Central topic:** Error of regression-based GATE estimators under network interference, explained as exposure-mapping misspecification and corner-exposure extrapolation, with confidence intervals that undercover.

The existing bibliography already covers design-based estimation (Aronow, Ugander, HT variants), GATE designs, and regression-based GATE estimation (Chin, Han and Ugander). No queries are spent there. The gap memo flags that area as well cited.

## Queries

1. **Misspecified exposure mapping** (`result_driven_theme`)
   - Query: *causal inference under misspecified exposure mapping network interference*
   - Target: `thesis-exposure-mapping-misspecification`, introduction, priority high. Anchor: "accuracy is governed by the fidelity of the fitted exposure mapping to the generating mechanism".
   - Rationale: Only Aronow2013EstimatingAC is cited for exposure mappings. The central thesis needs prior work on what goes wrong when the mapping is wrong.

2. **Unknown interference** (`result_driven_theme`)
   - Query: *average treatment effects under unknown interference structure*
   - Target: the same thesis target.
   - Rationale: This covers unknown or arbitrary interference. `Bhattacharya2019Uncertainty` already handles network uncertainty, so this query aims at estimand and bias results under unknown interference.

3. **Interference background and DiM bias** (`baseline_comparator`)
   - Query: *causal inference with interference spillover effects difference-in-means bias randomized experiments*
   - Target: `intro-interference-dim-bias`, introduction, priority medium. Anchor: "The difference-in-means (DiM) estimator, which is unbiased without interference, is systematically biased for the GATE under interference".
   - Rationale: The opening claims about no-interference violations and DiM bias have no foundational citation. Only HT estimators are cited there.

4. **Variance and intervals under network dependence** (`baseline_comparator`)
   - Query: *variance estimation and confidence intervals under network dependence in interference experiments*
   - Target: `reliability-interval-undercoverage`, results (reliability subsection), priority medium. Anchor: "ignores cluster dependence under the cluster design and uses no resampling".
   - Rationale: The 0.839 vs 0.95 coverage result is explained by HC1 intervals ignoring dependence. The draft cites no work on network-dependent variance estimation or HAC/cluster-robust inference beyond `Han2023ModelbasedRA`.

## Deliberately excluded
- Positivity/overlap extrapolation was a search topic in the gap target. It is folded into queries 1 and 2 rather than given its own query, to keep the set small.
- No GNN/Facebook100 queries, because the gap memo says they appear only as untested extensions in limitations.
- No retrieval was performed at this stage.
