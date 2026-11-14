# Reference Query Plan

**Central topic.** How much per-task targeted investment (score boost, measured by L1 depth and breadth over subtasks) a developer needs to make a target model rank first on public multi-task leaderboards (HELM MMLU 57 subjects, Open LLM Leaderboard 6 tasks), and how that minimal cost varies across aggregation rules.

## Core methods
- Minimum-cost boost plan solvers per aggregation rule (exact for mean/median/maximin/plurality; verified heuristics and MILP level selection for trimmed mean/Borda/Copeland/z-score)
- Exact-replica verification and verified boundary polishing (bisection shrink, redundant-drop, pairwise transfer) of boost plans
- Breadth-constrained cost (number of tasks boosted) vs depth (L1 total boost)
- Bootstrap CIs, task-subsampling robustness, Holm/Wilcoxon tests

## Comparator literatures
- Computational social choice: bribery, margin of victory, manipulation of voting rules
- Social-choice aggregation for multi-task/agent evaluation (Vote'n'Rank, Lanctot et al.)
- Benchmark-lottery / task-selection sensitivity
- Benchmark contamination and leaderboard gaming (Leaderboard Illusion, contamination papers)
- Robust statistics (trimmed mean, median breakdown point)

## Benchmarks
- HELM MMLU v1.13.0 (57 subjects)
- Open LLM Leaderboard contents/results (IFEval, BBH, MATH Lvl 5, GPQA, MuSR, MMLU-Pro)

## Shifts visible in the run
- Shift from heuristic per-rule search to exact/verified per-rule solvers, then MILP level selection for rank-based rules, then verified boundary polishing; grounded only in solver design, not in model architecture changes. Modest measured solver-efficiency gains: combined score 1.0018 -> 1.0034, all runs verified correct, plan validity rate 1.0.

## Result-driven themes
- Minimal investment depends strongly on aggregation rule (mean vs median vs min vs rank-based rules)
- Verified exact/near-exact plans with small gains from polishing over earlier heuristics
- Plausibility of targeted gains via data contamination or targeted training
- Uncertainty and robustness of conclusions to task subsets and snapshots

## Queries
1. `bribery and margin of victory in voting rules computational complexity` (core_method) — Minimal targeted boost to make a target rank first is a cost-minimizing manipulation/bribery problem; margin of victory and bribery are the closest formal analogues for the cost-vs-rule comparison (depth L1 cost, breadth cost).
2. `manipulation of Borda and Copeland rules complexity` (core_method) — Borda, Copeland and plurality are the rank-based rules solved by MILP level selection; their manipulation/bribery hardness motivates exact vs heuristic solvers.
3. `rank aggregation of multi-task benchmark scores with social choice rules (Borda, Copeland, maximin)` (baseline_comparator) — Comparator literature for the aggregation rules studied (mean, median, trimmed mean, min, Borda, plurality, Copeland); beyond starter items 5 and 11, includes Vote'n'Rank-style benchmark aggregation.
4. `robustness of rankings to task selection and aggregation choice in multi-task benchmarks` (baseline_comparator) — Reviewers expect connection to benchmark-lottery/task-sensitivity work: how rule choice changes who is first, which is the baseline for the paper's rule-dependence claim.
5. `trimmed mean median robust location estimator breakdown point` (core_method) — Mean, median and trimmed mean differ in how many per-task boosts are needed; breakdown point/influence function theory explains the predicted cost ordering.
6. `benchmark contamination training on test data inflates language model leaderboard scores` (result_driven_theme) — Targeted investment is modeled as including subset-related data in training; contamination/leakage literature supports the plausibility and magnitude of per-task score gains.
7. `adaptive overfitting and holdout reuse in machine learning leaderboards` (result_driven_theme) — Strategic targeting of leaderboard components is a form of overfitting to the evaluation; Ladder/holdout-reuse work frames leaderboard gaming and limits of the claims.
8. `Open LLM Leaderboard IFEval GPQA MuSR MMLU-Pro BBH MATH benchmark suite` (benchmark_context) — Scientific context for the 6-task Open LLM Leaderboard data used; the task components need citations.
9. `HELM MMLU 57 subjects per-subject scores language model evaluation` (benchmark_context) — 57-subject HELM MMLU v1.13.0 is the many-task setting; the dataset and evaluation framework need accurate citations.
10. `confidence intervals and uncertainty for model rankings on leaderboards bootstrap` (result_driven_theme) — The run reports bootstrap CIs and subsample-task robustness over rankings; ranking-uncertainty literature supports the methodology.

## Forbidden patterns
- Any query naming or paraphrasing the withheld published paper on this exact research question (title, authors, results), or pages citing/discussing it
- Generic: benchmarking, optimization, scientific method, paper writing
- Chronology/search-history phrasing (cycles, attempts, incumbent scores)
- Model-architecture queries (transformer, scaling) — no architectures are trained
- Starter-literature titles already supplied (MMLU, BBH, HELM, Benchmark Lottery, Lanctot, Leaderboard Illusion, Zhou, Yang, lm-eval-harness, Handbook of COMSOC) except to resolve BibTeX

## Notes
No prior references provenance existed. Grounding: paper_data.json shows 3 solver variants, all verified correct (combined 1.0018, 1.0018, 1.0034; final sealed eval ≈1.0026), no ablations directory. Queries stay in social-choice manipulation, benchmark aggregation, contamination, and leaderboard-data context. Generic alternatives (e.g. 'benchmarking', 'optimization') were rejected as non-specific. No retrieval performed.
