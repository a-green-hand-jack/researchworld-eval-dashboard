# Mild exponential annealing: interface-limited candidate

Attempt: `cycle_03_mild_exponential_annealing_attempt_01`  
Idea: `cycle_03_mild_exponential_annealing`  
Program: `program_1`

## Implemented control

Cloned `program_0` with its unchanged `program_spec.toml` and `program.py:handle`
entrypoint. Every valid seed and workload receives `initial_lr=0.01` and
`decay_rate=0.5`. The only numerical policy change is decay_rate from 1.0 to 0.5.
The required clipped exponential schedule uses step/steps, not block index.
Validation and reset/recipe/schedule state transitions are preserved, with
formatting and equivalent decimal spellings matching the required snippets.
Responses contain only the documented fields. No feedback or diagnostics are
added, and seeds do not select recipes.

## Falsifiable hypothesis and limitations

The hypothesis is that this mild annealing policy improves the canonical
aggregate over the constant-rate incumbent by retaining larger late learning
rates than strong annealing while reducing late update size relative to a
constant rate. The supplied incumbent aggregate is 0.0013285757680326544;
the supplied strong-annealing aggregate is 0.0012374734382319728. These are
task-provided historical observations, not measurements made in this stage.
The official improvement gate compares against the incumbent, not the lower
strong-annealing score. Neither monotonicity nor significance follows from
these observations.

Widths, operations, datasets, optimizer and weight-decay arms remain owned by
the evaluator. This interface exposes neither trajectories nor independent
uncertainty estimates. Changing learning rates also changes cumulative AdamW
shrinkage, so any aggregate improvement cannot isolate optimization from
regularization or establish a width-dependent grokking mechanism. This
candidate does not fulfill the full paper-level research task.

## Preparation and evaluation status

Only filesystem preparation and static inspection were performed. No candidate
code, tests, training, evaluation, benchmarks or optimizers were executed.
There is no new measured score, correctness result, confidence interval or
scientific conclusion. The harness will run the official evaluation after
preparation. No external sources were retrieved or forbidden literature
encountered. Reproduction of this controller uses the starter's documented
reset, recipe and ordered schedule requests without additional inputs.
