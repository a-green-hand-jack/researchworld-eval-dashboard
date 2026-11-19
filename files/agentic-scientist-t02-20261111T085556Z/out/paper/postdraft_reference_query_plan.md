# Post-draft reference query plan

**Status:** ready. The gap memo justifies a targeted pass on three paragraphs, giving six queries. Nothing else in the draft needs new citations.

**Central topic:** how grokking delay on modular addition depends on transformer width. The gaps are the parametrization literature, prior empirical grokking work, and statistical methodology.

## Already covered (not searched)
Power, Nanda, Liu (Omnigrok), Varma, Kumar, Huang and Davies on grokking explanations. Memorization and double-descent citations (Zhang, Nakkiran, Tirumala, Morris). AdamW (Loshchilov). Lyle (RL effective learning rates) and Nam (dynamical richness) are cited but do not cover the width parametrization literature. Quantitative results are grounded in the evaluator artifacts and need no citations.

## Queries

### Gap 1: Related work, parametrization and optimizer scale (high)
1. `maximal update parametrization feature learning infinite-width neural networks Tensor Programs` (architectural_shift). This is the muP construction behind the width-dependent multipliers.
2. `hyperparameter transfer across width zero-shot tuning Adam learning rate scaling parametrization` (architectural_shift). It supports the effective-step-size argument under Adam used in the Discussion.

### Gap 2: Prior work on width dependence (high)
3. `grokking weight decay training data fraction time to generalization modular arithmetic` (baseline_comparator). It positions the paper against earlier empirical grokking studies.
4. `grokking initialization scale effective learning rate weight norm delayed generalization` (baseline_comparator). It covers the initialization-scale and effective-step-size confound.

Queries 3 and 4 avoid "model size/width and grokking delay" phrasing. The first-stage plan flagged that phrasing as risking the excluded prior paper. Direct width-dependence work will only appear if it surfaces through these weight-decay, data-fraction and initialization queries.

### Gap 3: Method, test statistic (medium)
5. `cluster bootstrap inference with few clusters percentile confidence intervals` (core_method). It supports the seed-cluster percentile bootstrap.
6. `regression with right-censored outcomes Tobit accelerated failure time bias of imputing censored values` (core_method). It supports the criticism of imputing the cap and the censored-analysis recommendation.

## Avoid
Re-searching the cited grokking explanations, memorization or double descent. Also avoid chronology or harness terms, LLM scaling-law queries, and explicit "effect of model size on grokking delay" phrasing.
