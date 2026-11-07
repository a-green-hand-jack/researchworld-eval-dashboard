# Candidates

| Subgoal | Candidate | Idea | Verdict | Issue Or Reason | Internal rounds |
|---|---|---|---|---|---|
| g1–g2 | C1 | Condition on pilot and exogenous learner seed, then apply finite-population inclusion probabilities | sound | Gives exact design mean and finite-population variance, including singleton-complement census | 2 |
| g2 | C2 | Apply the same theorem with roles reversed and fixed linearity | sound | Fixed half weights need no equality of sizes and no directional independence | 1 |
| g4 | C3 | Stress unrestricted learner randomization using independent Cauchy scaling | sound | Refutes unconditional unbiasedness without integrability; does not affect deterministic finite ridge | 2 |
| g3 | C4 | Trace fit, aggregation, source strata, allocations and runner; run only supplied tests | sound | Structural match under ideal design; seeded conditional uniformity is not established by code or tests | 2 |
| g4 | C5 | Test census, unequal sizes, dependent directions and union-membership nuisance by exact hand examples | sound | Census exact; half average unbiased but not generally pooled sample mean; membership leakage can bias without labels | 2 |

No web, delegated agent, experiments, or implementation changes. Existing regression tests: 9 passed in 4.58 seconds. Numerical tests support only the checked implementations/cases, not the general proof.
