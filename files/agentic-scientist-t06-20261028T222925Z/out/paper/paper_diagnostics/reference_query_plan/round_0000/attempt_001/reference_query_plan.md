# Reference Query Plan

**Status:** ready

## Central topic
How few comparisons must be **dropped** or **flipped** to change the **top-1** or **top-k set** of a Bradley-Terry leaderboard, compared across evaluation designs: crowdsourced votes (Chatbot Arena 140k), expert humans vs GPT-4 judges (MT-Bench), and sports (NBA 2014/2015). Synthetic and permutation controls are included.

## What the run grounds
- The final evaluated configuration is identical to the baseline (`source_evidence/downstream/program` == `baseline`). It is a one-step influence (AMIP-style) ranking of rows by their first-order effect on the leader-challenger margin. An exponential + binary prefix search with exact ridge-BT refits then verifies the result. Three seeds give identical verified sizes.
- Verified sizes for the top-1 target (drop / flip): Arena-140k 62 / 46 (≈0.046% of rows dropped); MT-Bench human 92 / 46 (≈2.7%); MT-Bench GPT-4 143 / 61 (≈6.0%); NBA 2014 7 / 4; NBA 2015 16 / 8 (NBA ≈0.9%). Top-k sets are more fragile: Arena top-5 drop is 21, and NBA top-5 drop is 1.
- Influence-guided sets are ≈16× smaller than random sets (mean log2 ratio ≈3.98, CI [3.93, 4.0]).
- Three refined variants (category-count relinearized knapsack, swap refine, seeded prune) failed on harness infrastructure before they ran. They are **untested**, so no query treats them as a contribution.

## Query set (9)
| # | Category | Query | Why |
|---|---|---|---|
| 1 | core_method | approximate maximum influence perturbation dropping small fraction of data robustness | AMIP is the search behind every number; we also need follow-ups on exact/certified bounds to justify calling the sizes upper bounds |
| 2 | core_method | influence functions infinitesimal jackknife approximate leave-one-out generalized linear models | grounds the one-step Newton/influence score for the logistic-type BT likelihood |
| 3 | core_method | Bradley-Terry model maximum likelihood estimation existence MM algorithm paired comparisons | the estimator, its existence conditions under dropped rows, and how it is fitted |
| 4 | baseline_comparator | top-K ranking from pairwise comparisons sample complexity spectral MLE | theory for top-k identifiability; ties to our top-k targets and the role of the margin |
| 5 | baseline_comparator | adversarial manipulation of rank aggregation from pairwise comparisons | flip/drop sets are poisoning attacks; the closest comparator to vote rigging |
| 6 | benchmark_context | Chatbot Arena crowdsourced pairwise human preference LLM evaluation leaderboard | context for the main crowdsourced dataset and its known critiques |
| 7 | benchmark_context | LLM-as-a-judge agreement with human expert pairwise judgments biases | explains why human vs GPT-4 judges differ in fragility on MT-Bench |
| 8 | benchmark_context | Elo rating predictive accuracy professional sports paired comparison | the sports-design control (NBA) |
| 9 | result_driven_theme | confidence intervals uncertainty quantification Bradley-Terry ranking bootstrap | contrasts sampling CIs with worst-case data-dropping fragility |

## Rejected alternatives and why
- **Title-like queries** ("leaderboard stability under data perturbation", "sensitivity of Bradley-Terry rankings"). These risk surfacing the forbidden prior study or pages that cite it, so they are excluded by the task rules. The component-literature queries above cover the same ground without that risk.
- **Generic queries** ("robust optimization", "LLM benchmarking survey", "machine learning evaluation"). They have low precision and no tie to influence, BT, or manipulation.
- **Knapsack / Frank-Wolfe / relinearization queries.** These describe the untested variants and are not grounded by any evaluated result.
- **Chronology / infra queries.** Excluded per the planning rules.

## Forbidden patterns
See `forbidden_query_patterns` in the JSON: title copies of the research question, "who cites / follow-ups of Huang et al." queries, generic filler, chronology or variant-name queries, and queries that present untested variants as validated.
