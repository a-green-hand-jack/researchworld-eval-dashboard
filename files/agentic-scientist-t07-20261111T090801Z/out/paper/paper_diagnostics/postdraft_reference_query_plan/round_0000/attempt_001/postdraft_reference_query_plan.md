# Post-draft Reference Query Plan

**Status:** ready. Central topic: predicting a new LLM's full-benchmark score from a small, source-informed item subset (IRT-style logistic latent model, Fisher-information D-optimal selection, model-assisted difference estimator), focused on targets stronger than all source models.

The gap memo flags three targeted gaps. Comparator, benchmark and stacking citations are already adequate, so this plan adds no queries for them. It has four queries in total.

## Queries

1. **Strong-target extrapolation** (`result_driven_theme`, high priority)
   - Query: *predicting benchmark performance of new stronger language models extrapolation beyond source model range*
   - Gap: `intro-strong-target-motivation`. The introduction's central framing, that the better-than-all-sources case is the hardest and most practically relevant, has no citation. The only related cite, Zhang et al., is used for data rather than for this point.

2. **IRT and Fisher-information item selection** (`core_method`, medium priority)
   - Query: *multidimensional item response theory Fisher information item selection computerized adaptive testing*
   - Gap: `related-work-irt-fisher-design`. The logistic latent model and Fisher-based design currently rest only on Rodriguez et al. and Kiefer. This query looks for foundational multidimensional IRT, MAP ability and CAT item-selection sources.

3. **Model-assisted survey estimation** (`core_method`, medium priority)
   - Query: *model-assisted survey sampling difference estimator regression estimator*
   - Gap: `related-work-model-assisted-estimator`. The estimator is the classical survey-sampling difference estimator, but only prediction-powered inference is cited.

4. **Modern descendants of the difference estimator** (`core_method`, medium priority)
   - Query: *PPI++ efficient prediction-powered inference active statistical inference labeled sample model predictions*
   - Gap: same paragraph as query 3. It adds one or two bridging citations beyond the existing prediction-powered inference paper.

## Deliberately excluded
- Benchmark-subset comparators (anchor points, tinyBenchmarks, metabench, PromptEval, ONEBench, adaptive methods), benchmark sources, stacked generalization and the D-optimality equivalence theorem. The gap memo marks these as adequately supported, and adding more would only pad the bibliography.
