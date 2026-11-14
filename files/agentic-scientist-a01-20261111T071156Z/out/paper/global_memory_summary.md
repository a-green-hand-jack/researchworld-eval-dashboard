# Global Memory Summary

Use as qualitative context only; do not use as quantitative grounding source.

## Recent Entries

- 2026-11-11T00:00:00Z | step=idea | scope=idea
  - summary: Selected idea c01_min_boost_cost_by_aggregation: minimal targeted per-task boost (depth L1 and breadth) for a target model to rank first, compared across aggregation rules (mean, median, trimmed mean, min, Borda, plurality, Copeland) on HELM MMLU v1.13.0 and Open LLM Leaderboard. Alternatives considered: pure theory of rule manipulability (no empirical grounding), strategic-equilibrium game model (too close to starter lit item 9 and heavier), contamination-spillover regression (needs per-model training data not public). gate=kept; trigger=none; reason=no empirical evidence yet to justify a conclusions update.
  - evidence: No execution at idea stage; derived from task context. Rubrics: combined_score_exceeds_incumbent (metric), multi_rule_exact_solvers_verified (implementation), breadth_depth_and_uncertainty_reporting (implementation), public_data_manifest_and_robustness_ablations (implementation).
- 2026-11-11T08:21:02Z | step=implement | scope=program_1
  - summary: program_1 ready: per-rule minimal-investment solvers (exact for mean/median/maximin/plurality; verified heuristics for trimmed/borda/copeland/zscore) with exact-replica verification, pruning and starter fallback; offline helpers (manifest sha256, bootstrap_ci, holm/wilcoxon, subsample_tasks, run_ablations, breadth_constrained_cost). Untested: no execution allowed at this stage.
  - evidence: source edit only
- 2026-11-11T08:22:58.961904+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=1.0018272960697132, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 1.0018272960697132, "control_efficiency": 0.9967096937452276, "correct": true, "main_efficiency": 1.0031066966508344, "plan_validity_rate": 1.0}
- 2026-11-11T08:24:39Z | step=idea | scope=idea
  - summary: MILP level-selection solvers for borda/copeland/plurality/trimmed with verified cheapest-plan selection; gate=kept; trigger=none; reason=no new empirical evidence.
  - evidence: idea_bundle.json + target_rubrics.json written; incumbent combined 1.0018, control_efficiency 0.9967
- unknown_ts | step=unknown_step | scope=unknown_scope
  - summary: (missing summary)
  - evidence: (missing evidence)
- 2026-11-11T08:32:04.850122+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=1.0018272960697132, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 1.0018272960697132, "control_efficiency": 0.9967096937452276, "correct": true, "main_efficiency": 1.0031066966508344, "plan_validity_rate": 1.0}
- 2026-11-11T09:00:00Z | step=idea | scope=idea
  - summary: verified boundary polishing and transfer local search; gate=kept; trigger=none; reason=no new empirical evidence.
  - evidence: idea_bundle.json + target_rubrics.json
- unknown_ts | step=implement | scope=unknown_scope
  - summary: added verified boundary polish (bisect shrink, drop redundant, pairwise transfer, fallback) to program_1/src/program.py; not evaluated
  - evidence: (missing evidence)
- 2026-11-11T08:37:20.991926+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=1.003386466259221, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 1.003386466259221, "control_efficiency": 0.9967213029866018, "correct": true, "main_efficiency": 1.0050527570773755, "plan_validity_rate": 1.0}
