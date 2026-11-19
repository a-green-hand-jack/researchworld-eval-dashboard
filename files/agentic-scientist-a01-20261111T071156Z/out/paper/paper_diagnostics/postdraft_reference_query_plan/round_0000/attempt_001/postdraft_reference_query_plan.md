# Post-draft reference query plan

**Status:** ready. 4 queries, all driven by `draft_reference_gaps.json` (three rewrite targets). No retrieval was performed at this stage.

**Central topic:** The minimal per-task targeted investment (L1 score boost or L0 number of tasks touched) a target model needs to rank first on multi-task leaderboards under different aggregation rules, evaluated on Open LLM Leaderboard snapshots. The gaps are comparator literature in computational social choice, the missing citation for the held-out data source, and support for the introduction's incentive premise.

## Queries

### 1. Priced and swap bribery (`baseline_comparator`)
- **Query:** priced bribery and swap bribery in elections computational complexity
- **Target:** related work, "Computational social choice" paragraph (anchor: "Our problem is a continuous variant: the 'voters' are tasks...").
- **Rationale:** The paragraph cites only generic bribery, manipulation and margin-of-victory works. Cost-priced and swap bribery are the closest discrete analogues of the per-task investment model. They differ from the bibliography's Faliszewski2006, Xia2012 and Bartholdi1989.

### 2. Bribery and control under Copeland, Borda and plurality (`baseline_comparator`)
- **Query:** bribery and control complexity for Copeland, Borda and plurality voting rules
- **Target:** the same paragraph.
- **Rationale:** These are the rank-based rules the planner handles with heuristics or exact solvers. Rule-specific hardness results support the paper's different solution methods per rule. The existing citations cover ties and few candidates, not bribery under these rules. If results include score-based or range voting with per-voter costs, keep them.

### 3. Open LLM Leaderboard (`benchmark_context`)
- **Query:** Open LLM Leaderboard v2 Hugging Face evaluation of open large language models
- **Target:** related work, "The Open LLM Leaderboard aggregates six benchmarks", and the Data and splits paragraph.
- **Rationale:** All held-out results use leaderboard snapshots, but only the six component benchmarks are cited. Resolve to the leaderboard description or evaluation-harness documentation. Do not re-retrieve the component benchmarks or HELM.

### 4. Goodhart and leaderboard incentives (`result_driven_theme`)
- **Query:** Goodhart's law metric gaming and leaderboard incentives in machine learning benchmarks
- **Target:** introduction, "Rankings influence adoption, publication and funding, so developers have an incentive to act on them".
- **Rationale:** This is the premise of the study and currently has no support. One or two references are enough. Avoid near-duplicates of Singh2025, Chen2026, Ethayarajh2020 and Dehghani2021, which are already in the bibliography.

## Deliberately excluded
- Software citations (NumPy, SciPy, MILP solver) and planner heuristics such as bisection and greedy search. The gap memo does not flag them.
- The contamination and leaderboard-gaming paragraph, which is already densely cited.
- Any broader refresh of social-choice benchmark aggregation, robust statistics or ranking uncertainty. The existing bibliography covers these.
- Queries naming or paraphrasing a withheld published paper on this exact question.
