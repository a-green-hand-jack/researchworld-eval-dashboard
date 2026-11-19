# Reference Query Plan

**Central topic.** Estimation error of regression-based GATE estimators under network interference, framed as corner-exposure extrapolation bias versus variance across interference mechanisms, graphs and designs.

## Grounding
Three model variants were run: (1) a flexible ridge regression ensemble with extrapolation-aware selection (relative RMSE 0.232, worse than the linear baseline 0.184); (2) a linear base with shrunk design-weighted residual correction (0.185); (3) a BIC-gated parametric exposure-mapping library with linear fallback (0.140, bias 0.092, CI coverage 0.81). Baselines run: difference-in-means (0.62), Horvitz-Thompson (0.92), linear regression (0.18), oracle (0.05). Case 6 improved from about 0.71 to 0.27 with the parametric family; case 8 stays at about 0.45.

## Core methods
Regression-adjusted GATE; linear ridge baseline; design-weighted residual correction; BIC-gated parametric exposure mappings; design-resampling block/wild bootstrap.

## Comparators
Difference-in-means; HT/Hajek exposure estimators; graph cluster randomization; Han & Ugander regression adjustment; staggered rollout.

## Benchmarks
Synthetic SBM/BA/WS graphs; Facebook100 (Stanford3) and SNAP ego-Facebook only if used.

## Queries (10)
1. regression adjustment global average treatment effect network interference (core_method)
2. model-based regression adjustment network interference graph covariates bootstrap confidence intervals (core_method)
3. exposure mapping misspecification bias network interference total treatment effect estimation (result_driven_theme)
4. Horvitz-Thompson Hajek estimator general interference exposure probability variance (baseline_comparator)
5. graph cluster randomization network exposure bias variance tradeoff (baseline_comparator)
6. difference-in-means bias under interference randomized experiments SUTVA violation (baseline_comparator)
7. augmented inverse probability weighting doubly robust residual correction interference network (architectural_shift)
8. staggered rollout design total treatment effect interference without network knowledge (baseline_comparator)
9. extrapolation all-treated all-control counterfactual positivity violation network exposure (result_driven_theme)
10. Facebook100 social structure of Facebook networks (benchmark_context)

## Rejected alternatives
Generic queries (optimization, benchmarking, AI-scientist, chronology of attempts) and GCN/spectral-convolution queries were rejected: the run's methods contain no graph neural networks, so those starter-list papers are not supported by results. No query targets the excluded published paper.
