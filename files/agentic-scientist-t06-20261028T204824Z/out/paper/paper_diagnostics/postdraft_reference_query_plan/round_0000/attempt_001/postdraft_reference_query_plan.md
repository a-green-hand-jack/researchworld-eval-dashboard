# Post-draft reference query plan

**Status:** ready. Five queries, all driven by `draft_reference_gaps.{md,json}`; no retrieval performed in this stage.

## Central topic
Sensitivity of Bradley-Terry leaderboard rankings (rank-1 displacement) to small, evaluator-verified drop/flip edits across crowd, expert-human, LLM-judge and NBA sports designs. This plan only fills the three gaps exposed by the draft.

## Existing bibliography (not re-searched)
Bradley-Terry variants, ties/order effects, MLE existence, asymptotics and ridge fits; ranking uncertainty; Koh & Liang influence functions; Broderick et al. dropping-data robustness; Min et al. (vote rigging); Singh et al. (Leaderboard Illusion); Chiang et al. (Arena); Zheng et al. (MT-Bench).

## Queries

### 1. Poisoning and manipulation positioning (high, Related Work)
Anchor: "Influence and robustness to dropping data" and "Integrity of crowd-sourced leaderboards" paragraphs.
1. `influence function data poisoning attack training set perturbation logistic regression` (baseline_comparator): influence-based poisoning that chooses edits, the closest relative of the drop/flip probe.
2. `label flipping poisoning attack adversarial robustness pairwise comparison rank aggregation manipulation` (baseline_comparator): flip mode as a label-flip edit; adversarial robustness of rank aggregation.
3. `manipulation-resistant rating systems Elo Bradley-Terry strategic manipulation of match outcomes` (baseline_comparator): general manipulation of rating systems beyond the two Arena papers.

### 2. First-order group-removal accuracy (medium, Problem Setting and Method)
Anchor: "(i) Additivity. The per-row effects are summed without modelling how p_i and A change..." and the "Linearisation error" hypothesis.
4. `accuracy of influence functions for group effects removing multiple training points infinitesimal jackknife approximation error` (core_method): supports the claim that additive first-order approximations can be inaccurate at a 2% budget. One query covers both group-influence and infinitesimal-jackknife error.

### 3. Sports rating context (medium, Problem Setting and Method)
Anchor: Table 1 row "Sports: NBA regular-season games of 2008, 2012, 2015; home team listed first" and the "sports proxy" limitation.
5. `Bradley-Terry model home advantage rating of basketball and sports teams Elo` (benchmark_context): justifies NBA results as BT data and contextualises the home-first and tie conventions.

## Exclusions
- No re-retrieval of BT variants, ties, MLE existence, asymptotics or ranking uncertainty (the gap memo marks them over-supported).
- No re-retrieval of the Arena/MT-Bench data papers or already-cited influence, dropping-data and rigging papers.
- No queries about papers that directly study dropping preferences to change LLM leaderboard top ranks (excluded by the task's no-access rule).
- No claims about the re-linearised or prefix-search variants, since the run has no scored winner.
