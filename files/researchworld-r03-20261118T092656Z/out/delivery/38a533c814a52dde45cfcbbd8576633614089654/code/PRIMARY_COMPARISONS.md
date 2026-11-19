# Primary comparisons (declared before the confirmatory runs; written 2026-11-18)

Unit of replication: the held-out model. Per (model, k, selector, method) the mean standardised squared error
(`mse`, averaged over the model's targets and over repeated cross-fits; random selector averaged over >=100 draws).
Paired differences between two (selector, method) cells are computed per model, CI by bootstrap over models
(10,000 resamples), Holm correction over the family below, separately per matrix setting. Primary budgets: k in {3, 8, 20}.
Everything not listed is exploratory and labelled so in the paper.

Family (per setting; one test per row x k):
 P1. greedy A-optimal (`greedyA`, FA inference)         vs random (FA inference)
 P2. greedy A-optimal (`greedyA`, FA inference)         vs most-covered (setting B only; undefined in a complete block)
 P3. greedy A-optimal (`greedyA`, FA inference)         vs each of cluster / pivoted-QR / leverage / centrality (FA inference)
 P4. cost-aware greedy vs cost-ignorant greedy at equal total cost (error at matched cumulative cost)
 P5. FA posterior (selector `greedyA`)                  vs each of ridge / kNN / softImpute (same selector)
 P6. split-conformal stopping vs model-based stopping (coverage and stopping-k error; E6)
Added after a pilot (pilot = one 25-test-model cross-fit of A1 with a separate seed, rep 99, not in any result table;
it showed that the latent-variance objective `greedyA` overtakes random only at small k and degrades at large k):
 P7. `greedyAcomp` (expected total error on the complement; same FA) vs `greedyA` and vs random
 P8. `greedyGauss` + `gcov` (rank-free shrunk-covariance Gaussian conditioning) vs `greedyA` + FA, and vs random + `gcov`
P7-P8 are in the family (Holm counts them) but flagged "post-pilot" wherever reported.

H1 / H5 tolerances (relative RMSE gap 20% / 10%, rank_eff gap 2; >=90% of cells) are exactly those of
idea-repo `idea/method_and_theory.md` section 4 and are not changed.
Matrix settings are fixed by missingness only: A1 = full lowest-coverage peeling (103 x 202 complete); A2 = 30 most-covered
tasks x all models complete on them (126 x 30); B = tasks with >=40 models, models with >=5 such tasks (507 x 598, 22% observed),
test models with >=40 observed tasks. Test/history by repeated 5-fold partitions of models.
Hyper-parameters (FA rank by held-out likelihood, ridge/kNN/softImpute/shrinkage by inner predictive CV) are chosen on history rows only.

## Addendum, 2026-11-18 (declared before any group-transfer or cost result was inspected; the data of these runs were not opened)
H2's non-trivial targets get their own primary family, Holm-corrected within it, per matrix:
 G1. `greedyAT` (target-aware A-criterion, FA) vs random (FA), per target group, k in {3, 8}      (target = one task group, selected set drawn from the other groups)
 G2. `greedyAT` (FA) vs `greedyAcomp` (target-blind, FA), per target group, k in {3, 8}
 P4 (cost, as above): `greedyAcost` (FA) vs `greedyA` (FA, cost-ignorant) at total budgets of 5%, 10%, 20% of the summed
     median evaluation_time of all benchmarks; error of a model/selector at budget b = error at the largest grid k whose selected set costs <= b
     (mean predictor if none is affordable); random's cost is its mean over draws. Holm over the 3 budgets x matrices {A1, A2}.
E0 (leakage ablation: transductive vs history-only fitting) is reported as an exploratory paired difference at k in {3, 8, 20}.
Stopping rules (E6): tolerances eps in {0.5, 0.6, 0.7} (standardised RMSE) are exploratory conditions, not a tuned grid; k* censored at 60.
