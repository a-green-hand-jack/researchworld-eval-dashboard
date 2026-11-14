# Draft reference gap memo

**Status:** ready. A targeted post-draft retrieval pass is justified for three paragraphs. The rest of the draft is either well cited or grounded in `paper_data.json`.

## What is already adequate
- The grokking explanations in the introduction and the first Related Work paragraph (Power, Nanda, Liu, Varma, Kumar, Huang, Davies) are cited directly.
- All quantitative results (slope, interval, censored fraction, resolution limits) are grounded in the evaluator artifacts and need no citations.

## Targets

### 1. Related work, "Parametrization and optimizer scale" (high, background)
The evaluated model's key design element is a width-dependent multiplier meant to equalize the effective step size under Adam. The Discussion argues this could mask or create a width slope. The paragraph cites only an RL normalization paper and a dynamical-richness measurement paper. The standard width-aware parametrization literature is missing.
- Search topics: muP / Tensor Programs; hyperparameter transfer across width; Adam parametrization and effective step size.

### 2. Related work and introduction, prior work on width dependence (high, positioning)
The paper asks how grokking delay depends on model width. No cited work is positioned as having examined delay against width, size, weight decay, or initialization scale. The "Relation to this work" paragraph and the capacity-based reading both need this positioning. The memorization and double-descent citations are only indirect support.
- Search topics: grokking on modular arithmetic versus width and weight decay; grokking time versus model or data size; initialization scale and effective learning rate in grokking.

### 3. Method, test statistic (medium, background)
The statistic is a seed-cluster percentile bootstrap on delays right-censored at the cap, entered at the cap value. The Discussion recommends censored-data analysis. No methodological reference supports either choice or the remedy.
- Search topics: cluster bootstrap with few clusters; Tobit / accelerated-failure-time regression; bias from imputing censored values.

## Not requested
Stronger citations for memorization, double descent, or the individual grokking explanations. These are adequately covered and would only enlarge the bibliography.
