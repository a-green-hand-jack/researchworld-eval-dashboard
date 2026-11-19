# Plan

## Problem Type
Probability (primary), optimization and asymptotic statistics (secondary). Goal is an audit, not implementation or literature review.

## Goal
Independently audit /work/theory.md and the mathematical design in /work/todos.md. Produce /work/theory_audit.md with precise assumptions, defects, repairs, and complete proof sketches.

## Strategy
Use conditional binomial inversion, an exchange proof for the LP, orthogonal projection identities, and a finite-dimensional nuisance expansion; then counterexample-check the clean repaired statements.

## Subgoals
- [ ] g1: Check random counts, empty cells, and joint finite-sample coverage.
- [ ] g2: Check feasible weight optimization and multiplicity/selection.
- [ ] g3: Check oracle decomposition, equality cases, and no-gain scope.
- [ ] g4: Check same-data bin-mean estimation, variance estimation, and Wald qualifications.
- [ ] g5: Audit the locked design's inferential claims and report exact fixes.

## Intake Card
- Statement: the finite-sample construction and restricted-family variance results in theory.md, and inference procedures in todos.md.
- Variables: binary Y; measurable S in [0,1]; sample sizes n,N positive integers; confidence error alpha in (0,1); finite fixed M,K; p,w in [0,1].
- Explicit assumptions: independent iid labeled/unlabeled samples from the same law; predictor and prescribed partitions independent of evaluation; positive bin probabilities for the asymptotic claim.
- Declared defaults: n,N are nonrandom design sizes; partitions are measurable, disjoint, exhaustive, with boundary conventions; n tends to infinity in asymptotics. If external training is random, condition on it. In the full-data subsection the boundaries remain fixed and only bin response means are learned; genuinely learned boundaries require separate treatment.
- Blocking ambiguities: none that prevent an audit; missing hypotheses are findings, not silently granted conclusions.
- Edge cases: n_k=0, N_k=0, w_k=0, N=0 outside scope, constant S, constant Y, r=0, degenerate limiting variance, nonnested partitions, invalid denominator widths, random evaluation-learned boundaries.
- Needs user input: no.

## Notes
No web research, source traversal, experiments, code generation, or shell execution. EvoMath scripts are virtual /skills resources without a shell mapping, as specified by the user/runtime. Read the validator source using file tools and substitute explicit mental checks of its required fields; do not copy or implement scripts. Lightweight local clean-proof audit only, with no claim of multiple independent reviewers.

## Validation
Mental phase-1 validation PASS: Problem Type, Goal, Strategy are nonempty and Subgoals contains five filled g-numbered checkboxes. Structural validation is not mathematical validation.
