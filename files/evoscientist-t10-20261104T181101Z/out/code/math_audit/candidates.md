# Candidates

Proof mode; each route was reasoned through without computation, then revised and boundary-checked. Counts record local pencil-and-paper passes, not independent reviewers.

| Subgoal | Candidate | Idea | Verdict | Issue Or Reason | Internal rounds |
|---|---|---|---|---|---|
| g1 | C1 | Condition on bin memberships, then integrate random bin counts | sound | Binomial law is for count conditioning, not arbitrary conditioning on realized scores; zero-mass cells use [0,1] | 2 |
| g2 | C2 | CP empirical-frequency feasibility and pairwise mass exchange | sound | Exact box-simplex greedy LP; numerical tolerance alone cannot certify conservative endpoints | 2 |
| g3 | C3 | Center controls and complete the L2 square | sound | Gives restricted-family optimum and affine equality, not universal optimality | 2 |
| g3 | C4 | Test bin-number monotonicity on unequal partition geometries | sound | S uniform, Y=1{S<1/2}: K2 halves has zero approximation error, K3 equal thirds has error 1/12 | 2 |
| g4 | C5 | Express fitted-control remainder as a dot product of two finite-dimensional estimation errors | sound | O_p(n^-1) for fixed boundaries and finite n/N limit; prove scaled variance consistency separately | 3 |
| g4 | C6 | Test exact unbiasedness and zero leading variance | sound | Learned means need not give exact unbiasedness; r=0 deterministic-bin labels need a faster-rate argument | 3 |
| g5 | C7 | Treat MC coverage indicators as a separate binomial experiment | sound | Wilson is approximate; Bonferroni does not make it exact. Define width-ratio estimand and paired test family | 2 |

## Verified Claims
- Conditional-binomial CP plus a union bound proves the given finite-sample interval under the stated fixed-partition assumptions.
- Greedy endpoint optimization is exact over the box-simplex; selecting among all simultaneously covered intervals is valid.
- The oracle algebra, scalar optimum, and affine equality case hold in the control-estimator family.
- Fixed-K same-data fitted bin means are first-order oracle-equivalent; normalized plug-in variance consistency holds with the stated nondegeneracy condition.
- Bin-count monotonicity without refinement is false, by an exact population counterexample.

## Negative Attempts
- Do not infer conditional binomial sampling after conditioning on all observed score values.
- Do not infer partition refinement from a larger bin count.
- Do not infer studentized normality from a possibly zero root-n limiting variance.
- Do not infer exact simultaneous MC confidence from Wilson marginal intervals.

## Exact boundary checks
- K2/K3: E[m_B^2] is 1/2 for halves and 5/12 for thirds; subtract mu^2=1/4 to get explained variances 1/4 and 1/6, respectively.
- Learned-control finite-sample unbiasedness is not inherited: n=N=2, P(B=1)=1/4, Y=B. With global-mean fallback and shrinkage 1/2, the conditional expected estimates for labeled counts of ones 0,1,2 are 0,3/8,1. Their probabilities are 9/16,6/16,1/16, giving expectation 13/64, not mu=1/4.
- r=0 with deterministic bin labels is not a counterexample to first-order equivalence: the root-n limit is degenerate. If 0<mu<1, on occupied labeled cells the estimator equals the pooled oracle Bernoulli mean and has rate sqrt(n+N).

## Validation
Mental phase-2 validation PASS: candidate table has nonempty ideas and recognized verdicts, plus internal-round counts, verified claims and negative attempts. Exact arithmetic only; no experiments or numerical verification substituted for proof.
