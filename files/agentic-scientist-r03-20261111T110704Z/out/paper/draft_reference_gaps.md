# Draft reference gap analysis

**Status:** ready. The draft is well supported overall: the methods (EM, stacking, NNLS, submodular selection, ridge), item-level cheaper-evaluation work, and latent-capability work are all cited, and the quantitative claims are grounded in `paper_data.json`. Three targeted gaps remain. No retrieval was run in this stage.

## Targets

1. **related-work-comparators** (Related Work, high, comparator)
   - Anchor: "Low-rank and probabilistic matrix completion ... are the standard alternatives for filling score matrices"; "here the unit of selection is a whole benchmark".
   - The closest prior work predicts unrun benchmark scores from a few observed ones, applies low-rank or matrix-completion methods to LLM score matrices, or selects what to run adaptively. The draft cites only generic matrix-completion sources and item-level work. The paper's differentiation claim is therefore not positioned against its direct competitors.
   - Search topics: predicting LLM performance on unseen benchmarks from a benchmark subset; matrix completion or low-rank factorization of model-by-benchmark matrices; adaptive or IRT-based active selection for LLM evaluation.

2. **intro-benchmark-redundancy-claim** (Introduction, medium, positioning)
   - Anchor: "are known to overlap in what they measure".
   - The premise that motivates budgeted evaluation is cited only to the suites themselves, which do not document redundancy.
   - Search topics: correlation or redundancy among LLM benchmarks; low-dimensional structure in benchmark scores.

3. **data-open-llm-leaderboard-context** (Method, protocol data paragraph, medium, benchmark_context)
   - Anchor: "the Open LLM Leaderboard table (six benchmarks; 3371 history and 300 held-out models".
   - The leaderboard is one of three sealed evaluation datasets, and its six component benchmarks are named without citations. HELM and MTEB are cited.
   - Search topics: Open LLM Leaderboard v2 description; IFEval, BBH, GPQA, MuSR and MMLU-Pro papers.

## Missing literatures
- Cross-benchmark score prediction and matrix completion on LLM evaluation matrices
- Adaptive or IRT-based test and benchmark selection for LLM evaluation
- Open LLM Leaderboard and its component benchmarks
- Empirical evidence of benchmark redundancy

## Deliberately not flagged
- Rank-Gauss transform and kNN: standard components, and the draft already states them as such.
- Numeric results and protocol facts: grounded in evidence files.
- Limitations and discussion text: deliberately self-critical, with no external claims that need support.
