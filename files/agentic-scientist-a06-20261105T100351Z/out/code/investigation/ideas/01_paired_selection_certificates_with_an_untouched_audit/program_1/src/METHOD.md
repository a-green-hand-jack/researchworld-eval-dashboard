# Frozen-bank protected reporting policy

This candidate preserves the `python_rpc_v1:handle` contract. It returns exactly
the incumbent's 16 prompt strings, including the default reference at index zero,
and exactly the five documented update fields. The bank is frozen at module
initialization, hashed in order, and checked before returning a partition.
Reset/update state transitions and uniform reporting weights are unchanged.

## Implemented scope

Partitioning preserves the incumbent's seeded uniform shuffle of unlabelled slot
keys. Selection and report sets are checked for overlap and exhaustiveness. The
report subset is never used by the candidate for choice of prompts, tie priority,
or allocation. Neither stratum values nor key contents influence the allocation.

For multiple arms, the partition and RNG consumption are unchanged: selection
and report sizes remain one half each. For one arm,
selection cannot change the chosen configuration, so the minimum permitted
selection share (one quarter) leaves three quarters for reporting. This maximizes
the report sample size within the documented constraints, not an empirical
claim about the harness score. Stratified allocation was considered but not
adopted: it would add another untested methodological change, whereas preserving
the existing multi-arm policy avoids changing its selection/report tradeoff.
Wilson intervals remain evaluator-owned, not a candidate-derived guarantee.

## Unimplemented idea components

The process never receives outcomes, item-level correctness matrices, generated
answers, model revisions, actual search feedback, audit IDs, or population means.
It cannot compute paired differences, simultaneous empirical-Bernstein bounds,
selected-reference audit gains, or population coverage. The API fixes a bank of
16 rather than 24 prompts. It also fixes the reported estimator and interval.
Adding alternate estimators or diagnostic response fields would violate that API.
No search/report set is relabelled as an independent external audit. The external
audit remains outside this process; its disjointness cannot be checked here.

The implemented mechanism is therefore a protected reporting split over a frozen
bank, not a paired selection certificate or a completed scientific study. No real
inference, synthetic experiment, bootstrap, source verification of references,
paper compilation, or evaluation was run during this editing stage. No empirical
improvement, nominal coverage, or publication-ready result is asserted.

## Changed implementation paths

- `src/program.py`: frozen prompt manifest, protected random partition,
  single-arm reporting allocation, input and partition checks.
- `src/METHOD.md`: scope, rationale, and interface limitations.

The specification and entrypoint remain unchanged. The harness owns all actual
model calls, measurements, and final evaluation.
