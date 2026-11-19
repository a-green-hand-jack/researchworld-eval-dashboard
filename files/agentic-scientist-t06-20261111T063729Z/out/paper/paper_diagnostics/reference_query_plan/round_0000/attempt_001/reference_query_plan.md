# Reference Query Plan

**Central topic.** How few comparisons must be removed from a pairwise-comparison dataset to flip a Bradley-Terry leaderboard ranking (verified by exact refit), and how this differs across crowd-vote (Chatbot Arena), expert/LLM-judge (MT-Bench) and sports (NBA Elo) data.

**Grounded evidence.** Three search variants (row-level influence greedy; cell-aggregated relaxed search with swap polish; stationarity-LP over target ratings) tied on the search-stage score. Crowd-vote instances flipped with tiny budgets and the small expert table was not flipped within the cap. Influence-guided removal beat random removal, and permuted-outcome controls needed larger budgets. The final evaluation reported flip budgets on 52-model (135,630 rows) and 30-model (12,900 rows) tables.

## Queries (10)
1. Bradley-Terry model paired comparisons maximum likelihood estimation ranking (core_method): the model being refit.
2. approximate maximum influence perturbation dropping small fraction of data robustness (core_method): nearest methodological antecedent.
3. understanding black-box predictions influence functions (baseline_comparator): first-order influence machinery.
4. Chatbot Arena open platform evaluating LLMs human preference (benchmark_context): crowd-vote data and pipeline.
5. judging LLM-as-a-judge MT-Bench human expert pairwise judgments (benchmark_context): expert/judge data.
6. improving model ranking Chatbot Arena vote rigging (result_driven_theme): deliberate perturbation counterpart.
7. leaderboard illusion Chatbot Arena evaluation practices sampling private testing (result_driven_theme): leaderboard fragility context.
8. adversarial manipulation robustness rank aggregation from pairwise comparisons (baseline_comparator): general rank-aggregation robustness.
9. Elo rating system relation to Bradley-Terry sports game outcomes (benchmark_context): NBA design.
10. statistical inference uncertainty ranking from pairwise comparisons confidence intervals bootstrap (result_driven_theme): interpreting flip budgets against sampling noise.

## Rejected alternatives
Generic "benchmarking", "optimization" or "robustness of ML" queries, chronology-shaped queries about cycles, internal score names, and any query aimed at the withheld published paper on this question. The queries use method and dataset names that the run exercises. No query targets LP or convex-relaxation theory beyond what the Bradley-Terry and influence literatures already cover.

## Forbidden patterns
Generic surveys; process/paper-writing phrasing; search-history chronology; internal metric names; the withheld paper's title/authors/results or pages citing it; unrelated LLM architecture queries.
