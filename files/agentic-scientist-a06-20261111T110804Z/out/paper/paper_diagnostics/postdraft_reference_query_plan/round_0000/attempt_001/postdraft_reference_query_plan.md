# Post-draft reference query plan

**Status:** ready. No retrieval was run in this stage.

## Central topic
Quantifying and correcting the winner's-curse bias of reporting the best searched LLM prompt/pipeline configuration's score on the same benchmark questions used to select it, via searcher-agnostic debiased interval reporting evaluated on synthetic worlds and replayed MMLU-Pro outcomes.

## Approach
`draft_reference_gaps` flags three under-cited places in the current draft. Each gets a small, paragraph-specific query set (6 queries total). Adaptive data analysis, post-selection inference, scoring rules, Qwen2.5 and MMLU-Pro are already cited and are not re-queried.

## Queries

### 1. method-irt-model-background (high, background)
Anchor: "each logged outcome follows y_{qk} ~ Bernoulli(sigma(a_k - b_q))".
No IRT or Rasch work is cited, although the reporter is named EB-IRT.
1. `Rasch model item response theory logistic latent ability item difficulty` [core_method]: credits the IRT/Rasch foundations.
2. `hierarchical Bayesian item response model empirical Bayes marginal maximum likelihood Laplace approximation` [core_method]: ties the hierarchical-prior and Laplace empirical-Bayes fit to prior IRT estimation work. This is distinct from the existing Efron Tweedie and Stein entries.
3. `item response theory for language model benchmark evaluation question difficulty` [benchmark_context]: positions EB-IRT against IRT-based LLM evaluation, beyond the already-cited Polo2024EfficientMultiPrompt.

### 2. intro-selection-bias-ml-model-selection (high, positioning)
Anchor: "It is therefore a biased estimate of that candidate's accuracy on new questions, and the usual interval around it ignores the selection."
The ML model-selection literature is missing. Only Efron1997Bootstrap632 and Recht2019ImageNet exist on the ML side.
4. `over-fitting in model selection and subsequent selection bias in performance evaluation` [core_method]: supports the central bias claim.
5. `benchmark test set reuse overfitting meta-analysis repeated evaluation machine learning` [result_driven_theme]: empirical evidence of optimism after repeated test-set reuse.

### 3. related-work-prompt-optimizers (medium, comparator)
Anchor: "DSPy and MIPRO automate prompt and pipeline optimization".
6. `large language models as optimizers automatic prompt optimization` [baseline_comparator]: widens the comparator set beyond DSPy, MIPRO and Shi2024PromptBAI. Evaluation overfitting on small validation sets is covered only if results surface it.

## Out of scope
Generic hyperparameter-optimization or AutoML surveys, run chronology, and a broader bibliography rebalance. The forbidden query patterns from `reference_query_plan.json` are carried over.
