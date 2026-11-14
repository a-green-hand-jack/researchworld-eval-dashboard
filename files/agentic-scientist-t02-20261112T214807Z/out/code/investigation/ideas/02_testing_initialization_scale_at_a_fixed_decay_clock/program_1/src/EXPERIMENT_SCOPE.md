# Testing initialization scale at a fixed decay clock

Attempt: `cycle_02_initialization_barrier_attempt_01`  
Idea: `cycle_02_initialization_barrier`  
Candidate: `program_1`

## Current intervention and falsifiable prediction

Relative to `program_0`, this candidate changes only the training setting
`init_multiplier` from 1.0 to 0.5. Learning rate remains 0.003 and weight decay
remains 1.0. Every valid plan returns exactly these three common settings,
independent of width, seed, horizon, checkpoints, and resets. The manifest,
request validation semantics, response keys and types, and reset/plan state
transitions are unchanged. Source line wrapping is adjusted without behavior
changes. No extra diagnostics, training loop, or adaptive settings are added.

The prediction is improved finite-horizon mean final accuracy relative to the
incumbent. Unchanged or worse accuracy challenges this intervention. More
observed grokking or shorter restricted mean delay would additionally support
the delayed-generalization interpretation. Improved final accuracy alone does
not demonstrate grokking or distinguish immediate from delayed generalization.

Nominal AdamW multiplicative shrinkage per update is held fixed, not actual
weight norms or gradient dynamics. Initialization also changes activations and
optimization. A gain cannot identify norm mediation. A width-effect attenuation
prediction in matched-initial-norm controls remains untested unless public
arm- and width-resolved observations become available; no construction of that
trusted control is assumed. Aggregate metrics cannot establish width effects,
paired uncertainty, statistical significance, or clock collapse. Non-events
within the horizon do not imply permanent failure to generalize.

Only source inspection and filesystem comparison are permitted in this stage.
No tests, candidate execution, training, evaluation, or literature retrieval
are performed. No current measured results or uncertainty estimates are
available. Actual experiments, statistical analysis, the conference-template
paper and PDF, and complete measured reproducibility artifacts remain
outstanding. The harness owns the official evaluation after handoff.

## Historical scope from the preceding candidate (superseded)

The remainder is retained as a historical record of the preceding proposal,
not the current initialization setting, current hypothesis, or completed work.

# Separating width effects from a post-fit decay clock

Attempt: `cycle_01_width_decay_clock_attempt_01`  
Idea: `cycle_01_width_decay_clock`  
Candidate: `program_1`

## Implemented intervention

`program.py:handle` preserves the starter's reset/plan protocol, request
validation, response keys and types, and state transitions. Every valid plan
returns the same learning rate **0.003**, weight decay **1.0**, and initialization
multiplier **1.0**, regardless of seed, width, horizon, or checkpoints. Reset
clears episode state; precisely one plan is permitted after each reset.
`program_spec.toml` is unchanged. The module uses only standard Python and does
not launch experiments, write output artifacts, or inspect the environment.

The sole change to training settings from the starter is the learning rate
(0.001 to 0.003). These are configuration values, not measured results.

## Hypothesis and interpretation

The prospective hypothesis is that, among widths that fit the training set,
post-fit generalization delay is better aligned by positive AdamW decay
exposure than by update count alone:

    exposure = -(t_gen - t_fit) * log(1 - learning_rate * weight_decay).

Here this formula describes only the direct multiplicative decay component;
it is not an identity for actual weight norms under gradient updates.
The selected learning rate increases nominal exposure per update relative to
the starter while retaining its weight decay and initialization multiplier.
It can also change fitting time, stability, and gradient dynamics. No measured
performance improvement or isolated decay-mediated effect is asserted.

## Interface limitations

The actual permitted workload is addition modulo 97, a 0.6 training fraction,
widths 32/128/256, float32, and the
`two_embeddings_sum_gelu_linear_v1` architecture. The trusted trainer owns the
chosen, reference, zero-decay, and matched-initial-norm arms. The candidate
cannot redefine those arms, inspect their outputs, or change settings by width
or seed. It receives no examples, labels, trajectories, paths, losses, or
evaluation feedback.

Consequently the original prime-47, 30%-split, one-hidden-ReLU-layer proposal
is not implemented. Neither are its width-64 cell, three-decay factorial grid,
independently controlled seed streams, label-permutation controls, pilot-based
horizon, prime-59 confirmation, or initialization/logit diagnostics. Those
mechanisms are unavailable, not completed experiments. There is no shadow
training loop and no unused analysis module pretending to access observations.

## Scientific work still required

With separately authorized measured trajectories, the prospective analysis
would define fit and generalization by the first checkpoint starting three
consecutive accuracies at least 0.99. Missing events remain censored, not
assigned to the final checkpoint; generalization before fitting has zero
post-fit delay. A delayed event additionally requires a gap of at least 1000
updates and generalization time at least three times fitting time. Sensitivity
analyses would use accuracy 0.95 and ratios 2 and 5.

The proposed positive-decay equivalence criterion is a largest-to-smallest
width normalized restricted-mean delay ratio with its entire paired-seed 95%
interval inside [0.8, 1.25]. Intervals entirely outside reject practical
equivalence; overlap is inconclusive. Missing fits, scarce events, inadequate
common follow-up, or differing fit rates can leave the clock unidentified.
Zero decay cannot enter normalized-clock equivalence tests. A full test also
requires a controlled positive-decay contrast not offered by this interface.
Neither a score increase nor nonsignificance alone establishes equivalence.

The implementation stage forbids execution and external access. No training,
pilot, tests, evaluator call, literature retrieval, figures, empirical tables,
confidence intervals, or research findings have been produced. No paper PDF or
official-template source is supplied: the required evidence and verified
conference template are unavailable in this stage. A publication-quality
paper, measured runtimes, dependency-version record, failure ledger, raw
trajectories, and figure-to-script provenance remain outstanding research
deliverables, not claims made by this candidate. No prohibited literature was
accessed, and no references are asserted to have been read.

## Static review and handoff

The entrypoint remains `src/program.py` as specified by the unchanged manifest.
Only source text and the candidate directory contents were inspected; no
project code was executed or imported. The harness owns the subsequent
official execution. This file records the implementation's scope rather than
an empirical validation of the hypothesis.
