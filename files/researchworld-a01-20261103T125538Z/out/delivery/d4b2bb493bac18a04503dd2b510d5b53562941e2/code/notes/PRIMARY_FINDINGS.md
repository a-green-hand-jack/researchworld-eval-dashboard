# Completed primary evidence and claim limits

Run definition: every retained leaderboard entry is targeted once under every rule; selected task scores are set to 1; all other raw scores stay fixed; cost is the number of tasks selected; a tie for first counts. Results are a census of two frozen score matrices, not an independent random sample of models. Exact finite-snapshot quantities do not acquire meaningful sampling confidence intervals just by resampling correlated entries.

## What is established

`results/attacks_{helm,openllm}_primary.csv` records each target's certified optimum, selected task witness, bound and runtime. All 316 HELM and 18,300 Open LLM primary attacks returned optimal status. `src/summarize.py` generates the numerical presentation sources `primary_summary.csv`, `paired_rule_comparisons.csv`, `rank_strata.csv` and `budget_success_curves.csv`.

For HELM (79 entries, 57 tasks), median K across targets is mean 16, median 21, geometric 16, Borda 46; corresponding averages are 16.6962, 19.3165, 16.9241, 42.2278. For Open LLM (4,575 unflagged entries, six tasks), median K is 2, 3, 3, 6; averages are 2.36284, 2.84962, 2.98317, 5.51038. These are score-counterfactual task counts, not training measurements. K=0 is retained for each rule's existing winners; the summary also provides rule-specific nonwinner statistics.

Paired HELM comparisons: median costs more than mean for 64/79 targets, the same for 3, fewer for 12; Borda costs more than mean for 78/79 and the same for one. Open LLM: median costs more for 2,165/4,575, the same for 2,409, fewer for one; Borda costs more for 4,547, the same for 27, fewer for one. Starting ranks differ across rules; `rank_strata.csv` stratifies all rules by the same equal-task mean reference percentile. A general theorem that Borda always costs more is not established.

## Already completed critical sensitivity: HELM ceiling

The full HELM 12-configuration suite is complete in `attacks_helm_sensitivity.csv` plus the primary file. At alpha=1 with the observed per-task frontier ceiling, mean K averages 34.0886 while median K averages 19.3165, reversing their ordering by average cost relative to perfect scores. Geometric averages 33.2785 and Borda 43.5063. This is a material conditional/negative finding: a rule's apparent resistance depends on improvement ceilings, not only its aggregation formula.

At alpha=.5 and unit ceilings, success is infeasible even after changing all tasks for 39/79 mean targets, 38/79 median targets, 37/79 geometric targets, and 47/79 Borda targets. At alpha=.25 many more fail. Conditional mean K among feasible targets should never be interpreted as overall attack ease, since these sets differ by rule. Use success fractions and budget curves, or pair the identical feasible target sets.

## What is not claimed

The scores cannot establish achievable score uplift from adding data to training, true contamination status, dollar or compute budgets, cross-task transfer, simultaneous responses by other developers, or unobserved future benchmarks. Ceiling/frontier choices and alpha are explicit assumptions. Geometric aggregation depends on score origin and scale; raw-score sensitivity is required. Borda depends on the competitor pool; duplicate score/name sensitivity is required. Large-model training and evaluation were not performed.

## Completed supplementary analyses

All full uplift/ceiling/strictness and raw/inclusion/identity sensitivity runs, exact six-task and seeded HELM random task-order baselines, weighted-mean sensitivity, and 200 paired 45-of-57 distinct-subject subsets are complete. Full results and conditional claims are in `notes/ANALYSIS_HANDOFF.md`. The subset ranges describe perturbations, not confidence intervals for future benchmarks. Figure and report owners should make the ceiling-dependent reversal visible and label all assumptions in captions/methods.
