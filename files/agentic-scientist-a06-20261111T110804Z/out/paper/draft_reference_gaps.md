# Draft reference gap analysis

**Status:** ready. No retrieval was run in this stage.

## Overall assessment
The draft is well supported on adaptive data analysis (Dwork, Blum, Hardt and others), post-selection inference (Berk, Andrews, Efron) and the scoring-rule and Wilson baselines. Quantitative claims are grounded in `paper_data.json`, so they were ignored here. Three places are under-cited.

## Missing literatures
- Item response theory and latent-difficulty models, including their use in LLM evaluation.
- Selection bias and overfitting in ML model selection and hyperparameter search.
- Automatic prompt optimization beyond DSPy and MIPRO.

## Rewrite targets

1. **method-irt-model-background** (method, high, background)
   - Anchor: "each logged outcome follows y_{qk} ~ Bernoulli(sigma(a_k - b_q))".
   - The reporter is called EB-IRT, but no IRT, Rasch or hierarchical-IRT work is cited, and the empirical-Bayes and Laplace fitting is not tied to prior work.
   - Search topics: Rasch and IRT foundations; hierarchical Bayesian IRT with empirical-Bayes or Laplace fitting; IRT for LLM benchmark evaluation.

2. **intro-selection-bias-ml-model-selection** (introduction, high, positioning)
   - Anchor: "It is therefore a biased estimate of that candidate's accuracy on new questions, and the usual interval around it ignores the selection."
   - The central motivating claim has no support from the ML literature on model-selection bias. Related work covers statistics and holdout reuse, plus one image-classification study.
   - Search topics: overfitting in model selection; bias of cross-validation error when selecting among many models; meta-analyses of benchmark overfitting.

3. **related-work-prompt-optimizers** (related work, medium, comparator)
   - Anchor: "DSPy and MIPRO automate prompt and pipeline optimization".
   - The claim that no existing prompt-search work gives selection-aware uncertainty rests on only three cited works.
   - Search topics: LLM-driven automatic prompt optimization; evaluation overfitting in prompt optimization.

## Not flagged
- Adaptive data analysis, post-selection inference and scoring rules are already adequately cited.
- The ignorability and degenerate-world discussion is a design argument and does not need extra citations.
- Model and benchmark citations (Qwen2.5, MMLU-Pro) are present.
