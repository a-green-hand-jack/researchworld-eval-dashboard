# Statistical analysis specification (before main results)

## Target and sampling

The target is the population mean mu=E[Y]. Each replicate draws n iid labeled pairs (Y,S) and N iid independent scores S_U from the same population; S=f(X) is frozen. Every competing interval receives the identical draw. 'Fixed' means held fixed across methods within a replicate, not conditioning on one fully observed dataset while claiming a frequentist sampling probability. No new labels, predictors, or unlabeled observations are acquired by any method. Transformations of S are inferential control variates, not a change to f. Predictor training, calibration on external labels, adaptive labeling, and covariate shift are outside the model.

For real examples, the finite downloaded record list is explicitly the empirical superpopulation: sample labeled and unlabeled indices independently *with replacement*, use mean of all archived Y as truth, and never pass non-selected Y to any estimator. This is a sampling-distribution benchmark, not a confidence interval for a natural scientific population or a predictor-generalization validation. Duplicate records/indices are legitimate independent empirical-population draws. Ground-truth labels are used only by the evaluation harness.

## Estimator and exact variance algebra

For a deterministic function h, mu_hat(h)=mean_L(Y-h(S))+mean_U h(S) is unbiased, and
V(h)=Var(Y-h(S))/n+Var(h(S))/N.
Let r=n/N and m(S)=E[Y|S]. Constants in h cancel. Completing the square gives
V(h)=Var(Y)/n - Var(m)/(n(1+r)) + (1+r)/n Var(h-m/(1+r)).
Thus h*=m/(1+r) is optimal in this class, with V*=E Var(Y|S)/n+Var(m)/(n+N). This is a control-variate optimum, not an unconditional theorem that no imaginable confidence interval can be shorter.

For scalar controls h=aS, a*=Cov(Y,S)/((1+r)Var(S)); scalar PPI++ has no first-order loss exactly when m is affine in S (or when the selected richer space adds no projection signal). Let Pi_1 and Pi_p be centered L2 projections onto S and a nested fixed basis B. The variance improvement is [Var(Pi_p m)-Var(Pi_1 m)]/[n(1+r)]. The nonlinear improvement is nonnegative at population coefficients, but fitting can reverse it in finite samples. With no score signal h*=0 and label-only is optimal in this class. Finite N leaves the term Var(m)/(n+N), so free precision from arbitrarily many deterministic transformations is impossible.

## Implemented intervals and assumptions

- `label`, `ppi`, `ppi++`: Gaussian CLT intervals; PPI uses h=S. PPI++ matches the mean implementation of ppi-python 0.2.3: tuning numerator uses ddof=0 labeled covariance, denominator uses pooled ddof=1 score variance times 1+n/N, clipped to [0,1], and both variance components use ddof=0.
- `scalar_unclipped`: same formula without clipping, to separate basis improvements from implementation restrictions. It can outperform clipped PPI++ under negative or expansive calibration.
- `cf_linear`, `cf_cubic`: prespecified two equal folds. Fit centered ordinary least squares of Y on Legendre basis P_1(2S-1) or P_1,P_2,P_3 on the other fold; multiply coefficients by 1/(1+n/N). Apply to held-out labels and all unlabeled scores; average fold estimators. Interval variance uses the empirical variance of out-of-fold residuals /n plus variance of averaged fold controls on U /N. For fixed p, nonsingular covariance, consistent least-squares coefficients, finite second moments, and n,N increasing with positive finite ratio, this converges to the oracle fixed-basis normal limit. Cross-fitting does not itself prove exact finite-sample validity. Intercepts cancel and are omitted.
- `plugin_cubic` and degree-12 versions: overfitting diagnostics, with basis dimension fixed in advance and no choice based on results. `cf_degree12` checks that cross-fitting cannot remove estimation variance with too few labels. They are not automatically valid small-sample alternatives.
- All main Wald intervals are untruncated. Rare Bernoulli and t_3-noise scenarios deliberately probe CLT and nuisance-fit limitations. A zero-width Wald interval at all-zero labels is retained as a failure, never silently repaired or excluded.

## A genuinely finite-sample alternative for bounded data

For iid Z_i in an interval of known length R and k>=2, apply Maurer and Pontil (2009), Theorem 4, to Z and its reflection with error delta/2 each. With unbiased sample variance v, the two-sided radius is
b(Z,R,delta)=sqrt(2 v log(4/delta)/k)+7 R log(4/delta)/(3(k-1)).
The resulting interval covers E[Z] with probability >=1-delta without normality.

`eb_label` applies this to all n labels in [0,1]. For prediction-assisted versions, reserve the first floor(n/4) labels (at least 10) for training, and use only remaining m for the rectifier. Conditional on training, h is fixed. Let h lie in [0,c], so residual Y-h lies in [-c,1] of length 1+c. Apply b to residuals with delta=alpha/2 and to U controls with delta=alpha/2, add radii and intersect with [0,1]. A union bound proves >=1-alpha coverage under the stated independent iid sampling. No estimated noise bound is used.

`eb_ppi` has h=S (c=1); `eb_scalar` uses a training-only clipped scalar coefficient, shrunk by 1/(1+m/N), yielding 0<=c<=1. `eb_cubic` fits a training-only cubic with intercept, clips its output into [0,1], then shrinks by 1/(1+m/N). Both training and evaluation labels count toward the same original budget n. Label-only uses *all* n, so it benefits from not needing nuisance training. These conservative intervals need not beat normal approximations; comparisons between theorem-backed intervals use the EB baselines, and their additional price relative to Wald is reported honestly. The theorem does not require the regression model to be right.

## Uncertainty and comparisons

Each main cell has 5000 independent replicates with deterministic SeedSequence([20261102,scenario_ordinal,n,N/n,rep]). Nominal coverage is .95. Coverage gets a two-sided 95% Wilson Monte Carlo interval. Width gets mean and Monte Carlo standard error. Width ratio is ratio of paired sample mean widths; its SE is sd(W_A-ratio*W_B)/(sqrt(R)*mean(W_B)), not a mean of per-draw ratios. Ratios are never used to declare an invalid interval superior. They summarize precision conditional on a separate coverage assessment. Any coverage criterion over many cells is exploratory unless an explicit multiplicity correction is stated.

## Predeclared regimes

Synthetic scores are uniform on [0,1]. Linear and quadratic Gaussian regression, sigmoid regression, no signal, quadratic with t_3 noise, quadratic Bernoulli regression, and rare Bernoulli no signal are all included. n=100,500,2000, N=10n. Real frozen score data: galaxies, forest and alphafold from PPI example data v0.2.3. Main question: does the cubic beat scalar PPI++ while empirical coverage remains compatible with 95%, and where does it fail? A nonlinear positive case alone is insufficient; linear/no-signal null cases, small n and score distribution variation must appear in the report.

## Supplements specified before inspecting main results

- Exact Clopper-Pearson label-only intervals are added to all five binary-outcome regimes (two synthetic and three real) as an important genuinely finite-sample comparator. The sufficient count is recovered exactly from the saved label-only midpoint, with a numerical integer check; this avoids redoing any random experiment.
- A unit-PPI EB baseline that uses all n labels (`eb_ppi_full`) is added by deterministic seed replay, checked against the stored label-only mean. The common-split `eb_ppi` is retained to expose the cost of reserving training labels even for a fixed control. The full-label version is the stronger unit-PPI comparison.
- `bounded_quadratic`: Y=.025+.95(2S-1)^2+Uniform[-.025,.025], mu=.025+.95/3, n=2000/10000, N=10n, 3000 reps. This tests whether the theorem-backed EB approach can provide a finite-sample improvement in a high-signal bounded setting once its range penalties are less dominant. It is explicitly an added designed synthetic stress test, not an outcome selected from the main grid.
- Theoretical leading-order width ratios are computed by code/theory.py. Gaussian quadratic, linear, null, heavy-tail, quadratic Bernoulli and bounded quadratic cases have exact variance decomposition; sigmoid and real datasets are omitted from this exact table.

## Further robustness after the first real/bounded results

The first results showed real-data no-gain and small-n fit instability, plus a finite-sample gain in the designed high-signal bounded regime. To check the theoretical finite-N limitation directly, a follow-up uses the prespecified linear/quadratic/null generators at n=N=2000, 3000 paired repetitions each (`results/ratio1`). This is explicitly a follow-up rather than part of the original grid; the expected quadratic oracle ratio is approximately .775 rather than .524 at N=10n, with no asymptotic nonlinear gain in linear/null cases. All follow-up cells, including negative ones, will be reported.

## Context-checked comparator boundary

The published idea-repo Brief and Baseline-context pages were read after main analysis completion. Their source-checked distinction is adopted: original StratPPI changes/conditions on a stratified sampling design with fixed per-stratum counts and known masses. Our iid fixed-input benchmark has random stratum counts and estimated finite-N masses, so importing that variance formula or allocation benefit would not be a fair comparator. A bin-indicator control under this iid scheme could be implemented but is not part of the delivered grid; we make no superiority claim over poststratification, other nonlinear controls, or all existing valid-interval methods. The contribution is the conditional evidence within the stated scalar and bounded comparator families. Planning has now explicitly settled this boundary in story-repo#4: implemented baselines suffice for the narrow cubic-versus-affine question, no additional simulation is required, and StratPPI/poststratified adaptations remain discussed but unimplemented alternatives.
