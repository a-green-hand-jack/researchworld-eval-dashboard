# Draft Reference Gap Analysis

**Status:** ready. The draft already cites the benchmark-subset comparator families (anchor points, tinyBenchmarks, metabench, efficient benchmarking, PromptEval, ONEBench, the learned/adaptive methods and the benchmark sources). Quantitative claims are grounded in `paper_data.json`, so none are flagged. Three targeted gaps remain.

## Missing literatures
- Extrapolation of benchmark or ability prediction to models outside the source range.
- Item response theory and Fisher-information item selection in adaptive testing.
- Model-assisted difference estimation in survey sampling.

## Rewrite targets

1. **intro-strong-target-motivation** (introduction, high, positioning)
   - Anchor: "The hardest and most practically relevant case is a new model that is better than all sources".
   - The paper's central framing, the strong-target regime, has no citation. Prior evidence that benchmark prediction degrades out of range, or that new stronger models are the main use case, is needed.
   - Search: benchmark performance prediction extrapolation to stronger or newer LLMs; out-of-distribution or frontier model score prediction; failure of low-rank or IRT prediction under ability shift.

2. **related-work-irt-fisher-design** (related work, medium, background)
   - Anchor: "The latent model is an IRT-style logistic model fitted to a model-by-item matrix".
   - The multidimensional IRT, MAP ability and Fisher-information item-selection foundations are supported only by an NLP-leaderboard paper and Kiefer's result.
   - Search: multidimensional IRT logistic model; Fisher information item selection in CAT; D-optimal design for ability estimation in IRT.

3. **related-work-model-assisted-estimator** (related work, medium, background)
   - Anchor: "follows the model-assisted approach of correcting a model-based prediction with an observed-sample residual".
   - This is the classical survey-sampling difference estimator, but only prediction-powered inference is cited.
   - Search: model-assisted survey sampling difference estimator; PPI++ or active statistical inference.

## Not flagged
Benchmark citations, stacked generalization, the D-optimality equivalence theorem and the comparator paragraphs are adequately supported. Adding more would only pad the bibliography.
