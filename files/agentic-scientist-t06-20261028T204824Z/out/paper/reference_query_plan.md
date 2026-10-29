# Reference query plan

**Central topic.** Sensitivity of Bradley-Terry leaderboard rank-1 to small, evaluator-verified drop/flip edits of comparison data, compared across crowd (Arena 55k), expert/LLM-judge (MT-Bench) and sports (NBA Elo) designs.

**Grounding.** The task contract and starter program describe an adversarial drop/flip edit search against a ridge-BT refit, with random, win-rate, first-order-influence and constant baselines. The downstream investigation ended `completed_no_winner`, with the baseline (score ≈ 0.914) retained. Candidate variants (re-linearised greedy, pair-class multi-rival, rival-chunked prefix line search) were written but never scored. The plan therefore does not support claims of a better search method, and the queries stay on the sensitivity framing and its baselines.

**Queries (9)**
1. Bradley-Terry paired comparisons MLE (core_method): model and fitting background.
2. Approximate maximum influence perturbation, dropping a small fraction of data (core_method): drop-k robustness metrics.
3. Influence functions, black-box predictions (baseline_comparator): the first-order influence baseline.
4. Data poisoning / label flipping on pairwise-comparison ranking (baseline_comparator): flip mode.
5. Chatbot Arena vote rigging (benchmark_context): the intentional-manipulation threat model.
6. Chatbot Arena platform, human preference, BT (benchmark_context): Arena data pipeline.
7. MT-Bench / LLM-as-a-judge, human and GPT-4 judgments (benchmark_context): expert and judge design.
8. Elo vs Bradley-Terry, NBA sports (benchmark_context): the sports family.
9. Leaderboard ranking uncertainty and sensitivity to evaluation data (result_driven_theme): noise calibration and cross-design comparison.

**Rejected alternatives.** Generic "adversarial robustness", "benchmarking", "optimization" and "greedy search" queries were dropped as off-neighbourhood. Queries naming the re-linearised or prefix-line-search variants were dropped because they have no scored results. I wrote no query aimed at the specific excluded paper on dropping preferences to change top LLM rankings, and none should be added.

**Architectural shift.** From one-shot first-order influence ranking to iterative re-linearisation with exact-refit verification. This is a design attempt only, with no measured gain.
