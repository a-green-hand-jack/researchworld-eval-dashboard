# Proof Artifact

## Positive Lemmas

| ID | Statement | Proof Summary | Used By |
|---|---|---|---|
| L1 | Counts-conditioned label sums are binomial | Condition on iid category memberships, use conditional product law, then mix membership assignments with the same counts | Exact CP validity |
| L2 | CP inversion is conservative at every fixed sample size, including zero by [0,1] | Invert equal-tail binomial tests; random-count coverage follows by total probability | Exact response and mass bounds |
| L3 | Greedy box-simplex linear optimization is exact | Any mass assigned to a higher-cost coordinate while a lower-cost coordinate has capacity can be moved without increasing cost | CI endpoint construction |
| L4 | Simultaneous coverage survives measurable selection | The simultaneous event is contained in the selected interval's coverage event | Safe selector |
| L5 | L2 square completion identifies the control-family oracle | Cov(Y,h(S))=Cov(m(S),h(S)); complete square after centering | Oracle identities |
| L6 | Nested conditional expectations increase explained variance | Orthogonal projection and Pythagoras; nonnested dimensions have no order | Binning scope |
| L7 | Fitted finite-bin nuisance error is second order | Exact dot-product identity times two O_p(n^-1/2) vectors | Same-data equivalence |
| L8 | Scaled residual/unlabeled variance estimator is consistent | Uniform consistency on finitely many cells plus boundedness and two iid LLNs | Wald under nondegeneracy |

## Accepted Standard Facts
Equal-tailed CP inversion and its conservative binomial coverage; integer binomial mean is a median (used only for CP containing empirical frequency); finite-dimensional LLN/CLT, Slutsky, and Cauchy-Schwarz. The report gives the inversion and model-conditioning arguments rather than relying on literature. No external papers read.

## Negative Attempts

| Subgoal | Attempt | Reason To Avoid |
|---|---|---|
| g1 | Condition on exact observed scores | The Bernoulli success probabilities can vary with the score |
| g3 | More bins necessarily improve approximation | Requires refinement, not dimension alone; exact K2/K3 counterexample |
| g4 | Carry fixed-h unbiasedness to fitted h | Fitting is dependent on labels; exact n=N=2 bias counterexample |
| g4 | Divide by zero limiting variance | Root-n equivalence alone does not establish studentized normality |
| g5 | Bonferroni makes Wilson exact | Union bounds preserve marginal error guarantees, not approximations |
