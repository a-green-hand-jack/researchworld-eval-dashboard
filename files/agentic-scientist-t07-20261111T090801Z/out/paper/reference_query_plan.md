# Reference Query Plan

**Central topic.** Selecting a small subset of benchmark items using source models' per-item binary results, then predicting a new LLM's full-benchmark score and ranking. The strongest variant uses a logistic latent-ability model, Fisher D-optimal item selection, and a model-assisted difference estimator stacked with NNLS over source pseudo-target folds. It falls back to the incumbent estimator when source-only validation does not favour the stack.

**Core methods.**
- Model-assisted difference estimator.
- D-optimal/Fisher item design.
- Logistic (IRT-style) latent ability.
- NNLS stacking.
- Bagged/Laplace posterior-mean ability with tail correction. This last method gave no gain: its combined score was 0.9445, against 0.9452 for the plain stack.

**Comparators.**
- Anchor points.
- tinyBenchmarks (anchors + IRT).
- metabench.
- Active evaluation acquisition.
- Few-instance success prediction (assessors).
- The benchmark-prediction comparison study, which is on the starter list and so permitted.
- Random-subset mean.

**Benchmarks.** Open LLM Leaderboard v2 per-item data (IFEval, BBH, MATH Lvl 5, GPQA, MuSR, MMLU-Pro), HELM per-item data, and ARC-Challenge.

**Result-driven themes.**
- Strong (out-of-range) targets are about twice as hard as random targets. MAE is ~0.036 vs ~0.019, and Spearman ~0.82 vs ~0.96.
- Gains over random and anchor baselines are small in absolute MAE (~0.007–0.011) but consistent across the three variants.
- Source-only stacking addresses extrapolation.
- Posterior and tail calibration gave no additional benefit.

## Queries (10)
1. Anchor Points: Benchmarking Models with Much Fewer Examples (baseline)
2. tinyBenchmarks: evaluating LLMs with fewer examples (baseline)
3. metabench sparse benchmark reasoning knowledge LLMs item response theory (baseline)
4. Active Evaluation Acquisition for Efficient LLM Benchmarking (baseline)
5. How Benchmark Prediction from Fewer Data Misses the Mark (result theme)
6. predicting success of new LLM on unseen instances from few reference instances assessor (baseline)
7. model-assisted survey estimation difference estimator generalized regression estimator (core method)
8. D-optimal experimental design Fisher information logistic regression optimal item selection (core method)
9. stacked generalization non-negative least squares combining predictors (architectural shift)
10. Open LLM Leaderboard v2 IFEval BBH MMLU-Pro GPQA MuSR benchmarks (benchmark context)

## Rejected alternatives
- Generic "efficient LLM evaluation" and "benchmarking" queries. They bring in abundant but off-target citations.
- Campaign-history queries.
- Queries built on internal metric names.
- Any query targeting the withheld published paper on this research question.

## Avoid
No generic process, benchmarking or optimization queries. No chronology queries. No queries aimed at the withheld paper.
