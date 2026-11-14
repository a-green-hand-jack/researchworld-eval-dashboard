# Draft reference gap analysis

**Status:** ready. The draft is well cited on Shapley estimation, value-function semantics, stability measures and tabular data/models. All 26 `\citep` keys resolve in `references.bib`. Quantitative claims are grounded in `paper_data.json` and need no citations. Three narrow gaps justify a targeted retrieval pass.

## Missing literatures
- Run-to-run stability and per-instance uncertainty of sampling-based local explainers (LIME/SHAP).
- Delete-a-group jackknife variance estimation, and shrinkage/empirical-Bayes estimation.
- Use of feature attributions in deployed tabular decision settings.

## Rewrite targets

### 1. related-work-instability-comparators (high, comparator) — Related Work
- **Anchor:** "Local explanations are known to vary under perturbation and between methods ... Our label isolates a different and narrower source of variation".
- **Why:** The paper's core claim is a per-run reproducibility estimate for a stochastic explainer. The related work cites only generic robustness and disagreement papers, plus population-level uncertainty (Williamson2020Efficient). It does not cite work that measures repeated-run instability or per-instance sampling uncertainty of LIME/SHAP-style estimators. These are the closest comparators, and the novelty positioning is thin without them.
- **Search topics:** stability indices and repeatability of LIME under random sampling; confidence intervals or standard errors for Kernel SHAP and sampled Shapley estimates; reliability of SHAP across repeated runs and budgets.

### 2. method-jackknife-shrinkage-rationale (medium, background) — Method
- **Anchor:** "delete-one-group jackknife covariance"; "shrink the simulated value toward a budget-specific prior".
- **Why:** The diagnostic's two statistical ingredients have no cited source. Both topics were in the original query plan but did not reach the bibliography. One or two foundational references would ground the terminology without changing the story.
- **Search topics:** delete-a-group jackknife variance estimation; empirical Bayes shrinkage toward a prior.

### 3. intro-deployment-claim (low, positioning) — Introduction
- **Anchor:** "Shapley-value attributions are a standard way to justify an individual prediction ... in credit, medical and similar settings".
- **Why:** The deployment-practice claim ("run the explainer once and report what it returns") is supported only by the original SHAP paper.
- **Search topics:** explainable ML in deployment, and how practitioners use feature attributions.

## Deliberately not flagged
- Dataset citations (German Credit, Give Me Some Credit, Pima). The datasets are described with sources in the appendix, and extra citations would only add bibliography size.
- Shapley estimation variants and value-function semantics, which are already well covered.
- Deep tabular models, which are explicitly out of scope.
