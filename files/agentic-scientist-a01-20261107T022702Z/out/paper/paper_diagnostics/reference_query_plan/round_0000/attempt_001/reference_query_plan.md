# Grounded reference query plan

**Status: ready.** Eight queries; planning only. No references were retrieved or read in this stage. The named works below are task-supplied allowed candidates, not newly verified citations.

## Central topic and grounding

Study the minimum number of task-specific, bounded score increases needed to make a fixed target co-first under mean, ordinary median, and Borda aggregation. Selecting task `j` sets only the target score to `round(x_j + f(1-x_j), 10)`. Investment is support size, optionally normalized by task count. This is a hypothetical score-space intervention, not measured training expenditure, contamination efficacy, or an equilibrium among reacting developers.

Evidence inspected:

- `paper_data.json`: three evaluated search configurations, the selected downstream configuration, and separate final-evaluation allocations, reference bounds, and baselines. All three search configurations have equal recorded scores; no refinement superiority is established. The final evaluation is completed and qualified but has a different scope.
- `source_evidence/downstream/program/src/program.py`: exact mean and odd/even ordinary-median allocation, integer half-win Borda covering constraints, bounded branch-and-bound, and a greedy feasible fallback. The accompanying `METHOD.md` supplies assumptions, not empirical proof of later proposed refinements.
- `source_evidence/downstream/baseline/src/program.py`: greedy comparator. Final observations also contain random and no-update baselines.
- `task/resources/{search,final}/{helm,openllm}.json`: task lists, partition sizes, scaling, acquisition date, and licensing caveats. The final evaluator checks resource hashes and runs original, task-permutation, constant-score, and zero-response-copy cases.
- `figures/` contains no figure evidence. Neither `references.bib` nor `references_provenance.json` exists, so no prior queries need repair. Recent memory is private planning context only; prospective mixture cuts are not established findings of the selected executable.

## Methods and comparator literatures

Core methods are sorted headroom gains for the mean; threshold counts and middle-order-statistic endpoint enumeration for ordinary medians; rival-aware integer covering for Borda; and deadline-limited branch-and-bound with checked witnesses. Borda requires updating opponents' aggregate credits even though their underlying scores remain fixed. A feasible witness alone does not establish Borda optimality. Greedy, random, and no-update allocations are experimental comparators, not invented external algorithm families.

Reviewer-facing literature should cover social-choice evaluation, Borda manipulation/bribery with explicit non-equivalence caveats, benchmark-dependent comparisons, contamination, and strategic post-training. Generic optimization and unrelated model-architecture research are not needed.

## Benchmark context and architecture boundary

- **HELM/MMLU:** 57 subject columns; 37 search-partition and 42 final-partition model rows. The odd task count matters for the median formulation.
- **Open LLM Leaderboard:** six aggregate columns: IFEval, BBH, MATH Lvl 5, GPQA, MUSR, and MMLU-PRO; 2393 search-partition and 2129 final-partition model rows. Scores are divided by 100. The even task count matters; these are not six separately rerun model evaluations.
- Local resources record acquisition on `2026-11-07` and uncertain score-data redistribution permission. Dataset citations cannot establish the exact score snapshot or its license. The task-requested HELM release and Hugging Face revisions must be checked against acquisition records before the paper asserts them.
- **Architectural shifts: none.** Moving from cardinal scores to pairwise rank credits is an aggregation representation choice, not a neural-architecture or learned-representation transition. The JSON architectural-shifts list is deliberately empty.

## Result-driven priorities

Original final-evaluation observations support contingent rather than universal rule ordering. In the first recorded final episode, HELM target row `40` at `f=1` needs one task under the mean and zero under the median, while row `10` needs nine and twelve respectively. Open LLM row `1609` needs two mean versus three median tasks at `f=1`, but four versus three at `f=0.5`. These examples come directly from validated allocation records with exact reference budgets. They motivate contingent-comparison literature, not a claim that the median is always harder to influence.

At `f=0.5`, original cases include unattainable targets; at `f=1`, all sampled original-case targets have feasible witnesses. These are bounded-response phenomena, not evidence that training can realize either cap. Repeated final seeds operate on the same tables and are not independent population samples. Permutation and constant-score checks are controls, not composition-resampling experiments. No ablations establish benefits from gain-window or mixture-cut proposals. Search and final evaluation metrics must not be conflated.

## Query set

Only the exact titles below are proposed. Identifiers are copied from the task's permitted starter list, not retrieval results.

| # | Exact query | Category | Run-specific purpose |
|---|---|---|---|
| 1 | `"Evaluating Agents using Social Choice Theory"` | core_method | Borda/pairwise-credit evaluation context; allowed seed `arXiv:2312.03121`, not an allocation-certificate claim. |
| 2 | `"Handbook of Computational Social Choice"` | core_method | Borda, manipulation, and minimum-cost bribery foundations; DOI `10.1017/CBO9781107446984`. Do not equate ballot interventions with target-score updates. |
| 3 | `"The Benchmark Lottery"` | result_driven_theme | Context for contingent comparisons suggested by observed budget-order reversals; `arXiv:2107.07002`. Task selection is distinct from this run's rule/response changes. |
| 4 | `"Don't Make Your LLM an Evaluation Benchmark Cheater"` | baseline_comparator | Contamination motivation and the boundary between data exposure and hypothetical score caps; `arXiv:2311.01964`. |
| 5 | `"Leaderboard Incentives: Model Rankings under Strategic Post-Training"` | baseline_comparator | Strategic-interaction comparator to fixed rivals and one target; `arXiv:2603.08371`. No equilibria were evaluated here. |
| 6 | `"Measuring Massive Multitask Language Understanding"` | benchmark_context | The actual 57-subject benchmark and odd-median setting; `arXiv:2009.03300`. Not score-snapshot provenance. |
| 7 | `"Holistic Evaluation of Language Models"` | benchmark_context | HELM evaluation and score-table context; `arXiv:2211.09110`. Not proof of snapshot version or filtering. |
| 8 | `"A framework for few-shot language model evaluation"` | benchmark_context | Open LLM task-evaluation tooling context; DOI `10.5281/zenodo.10256836`. Not proof of exact harness version. |

These eight queries beat broad leaderboard-attack, optimization, benchmarking, and paper-writing searches: each has a specific methodological, comparator, or dataset role and a task-approved identity. Individual task papers are not exhaustively queried because the run allocates over six aggregate columns rather than studying each benchmark's internal methodology. Chatbot Arena/private-testing literature and contamination-detection algorithms are lower priority because neither human-preference data nor detection experiments appear in the run.

## Safety and retrieval handoff

No network retrieval, Semantic Scholar search, or `scholarly` call was made. Do not identify, guess, search for, access, or use the prohibited prior paper or anything citing/discussing it.

The unidentified exclusion makes unrestricted discovery unsafe. Later retrieval must be direct metadata resolution of the eight supplied allowed identifiers with exact-title agreement. Do not broaden the queries, expand citation/reference graphs, read related-paper recommendations, browse aggregation pages, or follow citing papers. Disable related-content previews; fail closed if the retrieval system cannot maintain this boundary. If excluded material is encountered accidentally, stop reading immediately and record its location and extent of exposure in reproduction documentation, without pursuing it further.

Also reject queries asserting architecture changes, causal training effects, universal rule robustness, new benchmarks from controls, or unmeasured solver improvements. Do not translate equal search scores or a separate final score into method superiority. Citation verification and reading are downstream work; this stage creates no bibliography, provenance file, paper source, or claims-grounding file.
