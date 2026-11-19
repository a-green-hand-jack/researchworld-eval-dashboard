# Global Memory Summary

Use as qualitative context only; do not use as quantitative grounding source.

## Recent Entries

- 2026-11-11T00:00:00Z | step=idea | scope=idea
  - summary: Selected influence-based greedy rank-flip budget search for Bradley-Terry leaderboards across Arena, MT-Bench, NBA; gate=kept; trigger=none; reason=first cycle, no results yet.
  - evidence: no prior history; baseline combined_score=0.499
- unknown_ts | step=implement | scope=unknown_scope
  - summary: re-linearised influence greedy + prefix bisection + drop-readd polish, exact-refit verified; offline datasets_offline.py added; untested
  - evidence: (missing evidence)
- 2026-11-11T07:31:26.961737+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.4993478260869565, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.4993478260869565, "control_gap_permuted_minus_real": 0.31530690537084394, "correct": true, "flip_rate": 0.5, "mean_budget_fraction": 0.5006521739130435, "reference_influence_score": 0.4993478260869565, "reference_random_score": 0.06947826086956523, "score_crowd": 0.998695652173913, "score_expert": 0.0}
- 2026-11-11T07:33:24.737784+00:00 | step=idea | scope=idea
  - summary: Cell-aggregated relaxed removal search + exact swap polish + small-k enumeration; fallback to cycle-1 row-level result. gate=updated; trigger=b; reason=new category: equal-to-incumbent result, expert instance unsolved.
  - evidence: cycle1 score_crowd=0.99870 score_expert=0.0 combined==incumbent; idea_bundle.json + target_rubrics.json written
- unknown_ts | step=implement | scope=unknown_scope
  - summary: cell-aggregated relaxed removal search + round/repair + exact swap polish + small-k enumeration on top of cycle-1 row-level safety candidate; files changed: program_1/src/program.py; untested
  - evidence: (missing evidence)
- 2026-11-11T07:40:05.782843+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.4993478260869565, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.4993478260869565, "control_gap_permuted_minus_real": 0.31530690537084394, "correct": true, "flip_rate": 0.5, "mean_budget_fraction": 0.5006521739130435, "reference_influence_score": 0.4993478260869565, "reference_random_score": 0.06947826086956523, "score_crowd": 0.998695652173913, "score_expert": 0.0}
- 2026-11-11T07:41:59.127783+00:00 | step=idea | scope=idea
  - summary: Stationarity-LP over target ratings for minimal removal sets; gate=kept; trigger=none; reason=new idea only, no new evaluation evidence.
  - evidence: cycles 1-2 tied incumbent 0.49935; expert unflipped; idea_bundle.json + target_rubrics.json written
- 2026-11-11T08:10:00+00:00 | step=implement | scope=attempt
  - summary: program_1 implemented: stationarity-LP over target thetas with exact rounding and fallback to row-level result; files: program_1/src/program.py; untested
  - evidence: (missing evidence)
- 2026-11-11T07:52:53.409235+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.4993478260869565, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.4993478260869565, "control_gap_permuted_minus_real": 0.31530690537084394, "correct": true, "flip_rate": 0.5, "mean_budget_fraction": 0.5006521739130435, "reference_influence_score": 0.4993478260869565, "reference_random_score": 0.06947826086956523, "score_crowd": 0.998695652173913, "score_expert": 0.0}
