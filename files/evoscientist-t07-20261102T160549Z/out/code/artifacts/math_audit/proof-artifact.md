# Proof Artifact

## Positive Lemmas

| ID | Statement | Proof Summary | Used By |
|---|---|---|---|
| L1 | Conditional audit sampling remains independent stratum-wise SRS without replacement after freezing pilot and exogenous learner randomness | Uniform disjoint fixed-size pair counting gives A_h uniform in U_h minus P_h; independent learner randomness does not change its law | Conditional mean and variance |
| L2 | Conditional directional mean equals the fixed bank mean | Inclusion probability a_h/(N_h-p_h) makes corrected residual expectation the full complement residual sum | Marginal unbiasedness under integrability |
| L3 | Conditional directional variance is N^-2 times the sum of M_h²(1-a_h/M_h)S_e,h²/a_h | Indicator variance and negative pairwise covariance give sample-mean variance; cross-stratum covariances vanish after conditioning | Directional variance |
| L4 | Fixed half average of swapped directions is marginally unbiased under first moments | Reverse uniform-pair argument plus linearity; no equal-size or independence assumption | Crossfit theorem |
| L5 | Unrestricted randomized wording has a moment counterexample | N=3,p=a=1,y=0,q_i=Z 1{i=3},Z Cauchy; directional output equals plus/minus Z/3 on an event of positive probability, so both signed expectations diverge | Literal-claim refutation |
| L6 | Actual ridge/direction code matches the integrable theorem for valid inputs and ideal randomization | Pilot-only xm/ym and coefficients; full fixed-source prediction sum minus pilot predictions; actual complement counts; no score clipping | Structural implementation verdict |
| L7 | Directions are not generally independent | N=4,p=a=1,y=(1,0,0,0),q=0 gives Cov(T1,T2)=1/32 | No independent-fold standard error |
| L8 | Unlabeled union-membership dependence can cause bias | N=3,p=a=1,y=0,q_i=1{i in P union A} gives T=-1/3 on every draw | Leakage warning |

All mathematical statements checked by exact algebra; L2/L4 require the moment qualifications in final.md. L6 is static code audit plus 9 supplied regression tests, not a proof of PRNG uniformity.

## Negative Attempts

| Subgoal | Attempt | Reason To Avoid |
|---|---|---|
| g4 | Infer an unconditional expectation from pointwise conditional design averaging with unbounded learner randomization | Fubini/tower can fail without integrability (L5) |
| g2 | Treat shared-label swapped directions as independent or condition the half-average on one pilot | Different conditioning sigma-fields; L7 gives a nonzero covariance |
| g3 | Call a five-seed coupled source/item run an exact uniform finite-population randomization | Fixed seeds are deterministic; conditional-on-source uniformity must be supplied by the design, not inferred from seed offsets |
