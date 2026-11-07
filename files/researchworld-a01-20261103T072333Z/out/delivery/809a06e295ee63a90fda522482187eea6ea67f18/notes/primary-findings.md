# Measured primary findings

Source: `results/attacks_helm.csv` (1,975 records) and `results/attacks_open_llm.csv` (114,375 records). All 116,350 cases completed. HELM: 908 analytic exact, 199 MILP optimal, 868 mathematically infeasible. Open LLM: 72,127 exhaustive feasible, 42,248 exhaustive infeasible. No unresolved optimum. Every feasible subset passed direct winning checks. Full run measured per-record compute totals were 27.935s (HELM including 256 random permutations) and 67.618s (Open LLM including exact random baseline); process startup/overall elapsed differs.

Under the full unit-ceiling intervention all targets are reachable. Median minimum counts over the full same evaluation cohort, including existing winners:

| Rule | HELM (79 targets, 57 subjects) | Open LLM (4,575 targets, 6 tasks) |
|---|---:|---:|
| Mean | 16 | 2 |
| Median | 21 | 3 |
| Geometric mean | 16 | 3 |
| Minimum | 11 | 3 |
| Borda | 46 | 6 |

These are descriptive finite-cohort medians, not population estimates or training costs. Per-target pair comparisons and distributions matter: a larger median alone does not prove universal dominance. Borda is materially more expensive under this primary score-space budget, while conventional robust cardinal summaries are not uniformly harder than mean. Random selection can be dramatically less effective than targeted selection, especially for the minimum rule: HELM mean random first-success count (censored at 58 if unreachable) is 50.46 versus optimized mean count 13.19. HELM random means are Monte Carlo estimates, not exact; do not quote extra decimal precision or infer score uncertainty from them.

Gain constraints change the interpretation. At alpha=0.25 and unit ceilings, reachable HELM counts are mean 9/79, median 11/79, geometric 9/79, minimum 21/79 and Borda 10/79. Open LLM counts are mean 558/4,575, median 427/4,575, geometric 841/4,575, minimum 4,575/4,575 and Borda 480/4,575. Conditioning medians on the reachable subset would compare different populations; use fixed-cohort reachability curves. The minimum's strongest rival is limited by its weakest task, so a low first-place threshold can permit bounded improvements to suffice even when other rules are unreachable.

The gain law assumes independent selectable task gains with no collateral change. This is an optimistic intervention menu and does not identify whether contamination or targeted training can attain a given improvement fraction. Cost is task count; the 57-subject and six-task budgets cannot be compared as equal training effort. No universal recommendation follows without these assumptions.

Robustness is complete: strict first place for the full grid, raw-score normalization and deduplicated-evaluation primary cohorts, 200 HELM task-bootstrap designs, six leave-one-task-out Open LLM designs. See `notes/robustness-findings.md` for results. Task composition variability is a sensitivity analysis, not sampling uncertainty of the published scores.

A common-challenger check removes the union of all rules' incumbent winners without excluding infeasible targets. In the primary setting this leaves 77 HELM and 4,571 Open LLM targets. HELM challenger medians for mean/median/geometric/minimum/Borda are 16/21/16/12/48; Open LLM medians remain 2/3/3/3/6. Borda never costs less than mean or geometric for these primary common challengers in either dataset. Its one Open LLM full-cohort exception against mean is its existing champion (zero versus one selected task). There remain common challengers where Borda costs less than median or minimum. Tables are `results/challenger_summary.csv` and `challenger_paired_rules.csv`. The empirical Borda-versus-mean ordering must not be promoted into a theorem for arbitrary score matrices.
