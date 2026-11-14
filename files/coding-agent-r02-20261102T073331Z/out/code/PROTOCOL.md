# Protocol, written before the main experiments

Research scope: prediction regions for an observed random continuous composition,
not class-label sets and not confidence sets for a latent probability inferred from
one class label. Synthetic-only, controlled evaluation. No claim of a new conformal
coverage guarantee. The added contribution is a boundary-aware evaluation and an
exact finite-calibration analysis of the extended CLR score.

Hypotheses: (H1) Euclidean, absolute, square-root and log-ratio geometries attain
marginal coverage under exchangeability but differ in normalized set volume;
(H2) unsmoothed CLR with structural-zero scores extended to infinity has a
binomial whole-simplex transition at zero prevalence near alpha;
(H3) pooled coverage hides group and boundary undercoverage; prespecified group
calibration repairs group coverage, not necessarily boundary coverage;
(H4) an explicit covariate-shift control breaks pooled validity and exact weights
repair marginal validity under this known shift.

Main design: five scenarios (dense, heterogeneous dispersion, structural zeros,
mixed dispersion/zeros, covariate shift), K=3,8,20, 100 independent repetitions,
pilot/calibration/test sizes 1000/499/2000, alpha=.1. The shift changes only
P(G=1) from .25 to .65. A fixed analytic center, identical for every method,
isolates set calibration; it is the Dirichlet mean before deletion of a component.
The pilot estimates group RMS Hellinger scales. No model tuning on test data.
Methods and DGP equations are implemented in src/core.py. Raw CLR is explicitly
infinite on the boundary; q=infinity means the entire closed simplex. Smoothing
uses log(y+epsilon) on both center and candidate; evaluate coverage of original y.
Coordinatewise 90% intervals are a deliberately invalid joint-coverage control;
Bonferroni intervals are the valid comparison. H-weight uses exact likelihood
ratios and the required test atom at infinity.

Efficiency: normalized uniform 2D simplex volume V2 and equal-mixture normalized
edge length V1, only for K=3. Randomized Sobol 2^14 joint samples over query
covariates and candidates per repetition; common random numbers across methods.
No volume conclusion is to be extrapolated to higher dimensions. Main interval:
two-sided 95% Student t interval over independent repetition-level means; paired
method contrasts use the same repetitions. Conditional metrics include G=0,
G=1, and observed zero/nonzero status. These are diagnostics, not simultaneous
confidence bands. Also report seed-level variability where helpful. Boundary
sweep uses Exp(1) finite scores and a zero atom at infinity, 4000 repeated
calibration arrays for each n in {99,499,1999} and each declared prevalence.

Changes, failures, and extra checks will be documented in RESEARCH_LOG.md.

Pre-main-run addition: include an oracle negative-log-density conformal baseline.
The analytic DGP density is taken relative to an equally weighted mixture of
normalized interior and codimension-one face measures. Deletion preserves the
Dirichlet law on remaining components with concentration vector kappa*m[-j].
The population density level set minimizes expected volume for this fixed
reference measure and marginal coverage; it is an unattainable practical baseline
when the conditional law is unknown. Report both V2/V1 and their .5/.5 mean.
