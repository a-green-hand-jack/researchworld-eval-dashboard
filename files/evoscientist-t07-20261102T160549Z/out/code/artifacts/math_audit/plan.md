# Plan

## Problem Type
Probability; finite-population, design-based estimation and static implementation audit.

## Goal
Audit the stated unbiasedness and conditional variance theorem and decide whether the supplied implementation satisfies its hypotheses. No web, code agents, experiments, implementation edits, or changes to /work/todos.md.

## Strategy
Condition on each pilot and audit-independent learner randomness, use stratified sampling-without-replacement identities, then trace implementation inputs and allocation rules against those hypotheses.

## Subgoals
- [ ] g1: Specify sampling sigma-fields and handle singleton-complement and census boundaries.
- [ ] g2: Prove directional unbiasedness, variance, and fixed-half swapped unbiasedness for unequal sizes.
- [ ] g3: Inspect source strata, extra allocation, direction/crossfit preprocessing and tests.
- [ ] g4: Adversarially check leakage, dependence, integrability and implementation limitations.

## Notes
Fixed disjoint strata partition a nonempty bank, binary labels fixed, positive integer p_h,a_h with p_h+a_h<=N_h. Treat algorithm randomness as exogenous conditional on pilots, independent of audit draws; distinguish a finite conditional nuisance vector from an unconditional moment assumption. Fixed seed means source-only seed for preprocessing/allocation, not conditioning away the sampling design. No blocking ambiguity; state moment qualifications explicitly rather than silently strengthening 'any randomized vector'.
