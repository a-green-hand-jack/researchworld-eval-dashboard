# Post-draft reference query plan

**Status:** ready. The gap artifact reports three targeted gaps, so this plan has six queries and no broader refresh. No retrieval was run in this stage.

**Central topic:** choosing k benchmarks to run on a new model and imputing its scores on the remaining benchmarks from a historical model-by-benchmark matrix (MTEB, HELM Lite, Open LLM Leaderboard).

## Existing bibliography (not re-searched)
The bibliography already covers tinyBenchmarks, metabench, anchor points, efficient benchmarking, Sloth, observational scaling laws and BenchBench. It also covers EM, stacking, NNLS, ridge, submodular selection, Bayesian design, IRT (Embretson, Vania), MMLU, BIG-bench, HELM and MTEB. None of these directions is repeated below.

## Queries

### Gap 1: related-work-comparators (high priority)
Related Work claims "the unit of selection is a whole benchmark" but is not positioned against benchmark-level competitors. The three queries cover the three directions named in the gap memo.
1. **baseline_comparator:** "predicting language model performance on unseen benchmarks from scores on a subset of benchmarks". This targets direct competitors that predict unrun benchmark scores from a few observed ones.
2. **baseline_comparator:** "matrix completion low-rank factorization of model-by-benchmark score matrix for LLM evaluation". The draft cites only generic matrix-completion sources (Candes, Salakhutdinov), so this looks for applications to LLM score matrices.
3. **baseline_comparator:** "adaptive testing item response theory active selection of evaluations for large language models". This targets adaptive or IRT-based selection of what to run, beyond the textbook and item-reduction work already cited.

### Gap 2: intro-benchmark-redundancy-claim (medium)
4. **result_driven_theme:** "redundancy and correlation among LLM benchmarks low-dimensional structure of benchmark scores". The claim that suites "are known to overlap in what they measure" is cited only to the suites. This looks for empirical redundancy or correlation analyses beyond BenchBench and Observational Scaling Laws, which are already cited.

### Gap 3: data-open-llm-leaderboard-context (medium)
5. **benchmark_context:** "Open LLM Leaderboard v2 evaluation of open language models". This finds a source for one of the three sealed evaluation datasets.
6. **benchmark_context:** "IFEval instruction-following, BIG-Bench Hard, GPQA, MuSR, MMLU-Pro benchmark". This finds sources for the six component benchmarks named in the protocol and appendix. BBH may already be partly covered by BIG-bench, and MATH Level 5 is not queried because the gap memo does not list it as a search topic. The retrieval step can resolve the individual papers.

## Exclusions
The gap memo deliberately does not flag the rank-Gauss transform, kNN, numeric results, protocol facts, or the limitations and discussion text. No queries are planned for these. Queries must not name or hint at the prior published paper on this exact task.
