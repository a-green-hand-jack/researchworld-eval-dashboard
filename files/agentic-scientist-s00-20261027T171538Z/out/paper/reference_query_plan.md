# Reference Query Plan

**Status:** ready

## Central topic
Predicting the expected cover time of simple random walks on small connected graphs (n ≤ 30) from a few cheap statistics (n, m, mean/max/min degree, diameter). The predictions are compared against classical worst-case bounds, with per-family error and Monte Carlo uncertainty reported.

## Grounding
- Final model (`source_evidence/downstream/program/src/program.py`): log-linear ridge regression `ridge_log_linear_v0` on log statistics plus a log n·log diam interaction. Final main log error is 0.183, identical across 3 seeds. The median Monte Carlo relative SE is 0.033.
- Evaluator comparators (`task/evaluate.py`):
  - AKLLR 2m(n−1): log error 1.84
  - Feige (4/27)n³: log error 1.60
  - best of the two bounds: log error 1.40
  - Matthews bound (max hitting time × H_{n−1}): 0.61
  - OLS reference: 0.53
  - constant predictor: 0.94
  - permuted features: 1.26
- Families: path, cycle, star, complete, grid, binary tree, lollipop, random tree, Erdős–Rényi, random 3-regular.
- Gains over the best bound by family:
  - largest gains (Δ ≈ −2.1 log units): complete, Erdős–Rényi, random 3-regular
  - smallest gain: lollipop (Δ = −0.11, CI [−0.22, 0.01])
  - largest residual error of the fitted model: grid, complete, Erdős–Rényi (≈0.36–0.38)
- The physics-mixture variant in memory was never evaluated. It is excluded from grounding.

## Queries (10)
1. **Comparator:** AKLLR "random walks universal traversal sequences complexity of maze problems". This is the 2m(n−1) bound.
2. **Comparator:** "tight upper bound on the cover time for random walks on graphs". This is Feige's (4/27)n³ bound.
3. **Comparator:** "Matthews covering problems for Markov chains hitting time bound". This is the matthews_ref comparator.
4. **Core:** "Lovász random walks on graphs survey". Starter literature that defines hitting, commute and cover times.
5. **Core:** "electrical resistance of a graph captures its commute and cover times". Explains why m, degree and diameter should be predictive.
6. **Result theme:** "Feige tight lower bound cover time n log n". The n log n regime is where the bounds are loosest.
7. **Benchmark context:** "cover time of random regular graphs and sparse random graphs Cooper Frieze". Covers the random 3-regular and Erdős–Rényi families.
8. **Benchmark context:** "cover times for Brownian motion and random walks in two dimensions torus". The grid family has a large residual error.
9. **Result theme:** "maximum hitting time for random walks on graphs lollipop". Lollipop is the extremal n³ family, where the model gains least.
10. **Core:** "Markov chains and mixing times Levin Peres Wilmer". Textbook reference for cover time and the Matthews method.

## Rejected / forbidden patterns
- **Queries that restate the research question** (e.g. "predict cover time from graph statistics regression small graphs"). These risk surfacing the forbidden original paper or pages that cite it.
- **Generic ML, CV or benchmarking queries.** They have no scientific specificity.
- **GNN or learned-embedding queries.** These methods were not used in the run.
- **Chronology queries.**
- **The unevaluated physics-mixture variant.**

## Why these beat generic alternatives
Each query names a specific comparator implemented in the evaluator, a graph family in the test set, or a family-level result: the largest gains in the n log n regime, the smallest on the lollipop, and the largest residual on the grid. No prior `references_provenance.json` exists, so there are no earlier off-topic queries to correct.
