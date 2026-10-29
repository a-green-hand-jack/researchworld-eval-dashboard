# Global Memory Summary

Use as qualitative context only; do not use as quantitative grounding source.

## Recent Entries

- 2026-10-28T23:30:00Z | step=idea | scope=idea
  - summary: Cycle 1 idea: exchangeable-row categories mean counts on p x p stats; relinearized Frank-Wolfe/knapsack greedy over category counts, multi (insider,outsider) pair targeting, exact-refit pruning, starter AMIP fallback. gate=kept; trigger=none; reason=no evaluation evidence yet.
  - evidence: Starter program_0 uses one-shot AMIP ranking on k vs k+1 margin only; incumbent combined_score=0.0 correct=true; no runs in idea stage.
- 2026-10-28T23:55:00Z | step=implement | scope=attempt
  - summary: Implemented relinearized category knapsack: _build_categories/_stats_from_counts category refits, _relinearized_greedy damped knapsack steps, _candidate_pairs multi-pair targeting, _prune_counts exact pruning, _verify_rows row-level safety check, _baseline_amip starter fallback (new set used only if strictly smaller and verified).
  - evidence: not executed; awaiting harness evaluation
- 2026-10-28T23:40:00Z | step=idea | scope=idea
  - summary: Cycle 2 idea: resubmit category-count relinearized multi-pair knapsack with prune + new 2-for-1 _swap_refine, governed by deterministic integer refit cap (_deterministic_refit_cap) instead of wall-clock gating; starter AMIP verified fallback. Cycle-1 attempt failed at harness infra (sandbox lease OSError) so method is untested, not refuted. gate=kept; trigger=none; reason=no evaluation evidence yet (infra failure only).
  - evidence: attempts_history.jsonl run_exit_code=1 rubric_status missing; wrapper_output.log OSError 'no owner-private directory is available for sandbox recovery'; starter code read; no runs in idea stage.
- 2026-10-28T23:59:00Z | step=implement | scope=attempt
  - summary: Implemented a deterministic relinearized category knapsack. Pipeline: _build_categories/_stats_from_counts for category-count p x p refits; _candidate_pairs for multi-pair first-order knapsack ranking; _relinearized_greedy for damped (0.65) relinearized steps; _prune_counts for binary-search plus single-unit exact pruning; _swap_refine for 2-for-1 unit swaps; _verify_rows for a row-level refit with 1e-7 safety. _baseline_amip provides the starter fallback, replaced only by a strictly smaller verified set. Effort comes from an integer cap from _deterministic_refit_cap (phases at 40%/75%/100% of the cap); the wall clock is only a 0.85*deadline backstop.
  - evidence: not executed; awaiting harness evaluation
- 2026-10-29T00:10:00Z | step=idea | scope=idea
  - summary: Cycle 3 idea 'Baseline-seeded exact pruning plus relinearized category knapsack'. The c01 and c02 attempts both failed with the same harness infra OSError (sandbox lease) before the program ran, so the method is untested. Resubmit the category-count relinearized multi-pair knapsack, and add an explicit _prune_baseline_seed that exact-prunes the starter AMIP count vector first within the guaranteed budget; this guarantees size <= starter and captures any first-order overshoot. Keep the deterministic refit cap, swap refine and row-level verification. gate=kept; trigger=none; reason=still no method evidence, only infra failures.
  - evidence: attempts_history.jsonl: both attempts run_exit_code=1, rubric_status missing, OSError 'no owner-private directory is available for sandbox recovery'. No runs during idea generation.
- 2026-10-29T00:40:00Z | step=implement | scope=attempt
  - summary: Implemented baseline-seeded exact pruning plus relinearized category knapsack in program_1/src/program.py. Components: _baseline_amip (the starter fallback); _build_categories/_stats_from_counts (p x p count refits); _prune_baseline_seed + _prune_counts (phase 1, 40% of cap: binary search plus single-unit exact pruning); _candidate_pairs + _relinearized_greedy (phase 2: damped 0.65 relinearized knapsack over 2-6 boundary pairs); _swap_refine (phase 3: 2-for-1 swaps); _verify_rows (row-level warm+cold refit, 1e-6*(1+|tol|) safety; must be strictly smaller than the starter). The integer cap comes from _deterministic_refit_cap; the wall clock is only a 0.85*deadline backstop; exceptions fall back to the starter set.
  - evidence: not executed (stage rules forbid local runs); rubric source patterns confirmed by grep; program_spec.toml identical to program_0
