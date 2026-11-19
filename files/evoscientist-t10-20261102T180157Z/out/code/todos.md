# Preregistered practical plan (before simulation results)

## Question and target
Estimate superpopulation mean mu=E[Y] for Y in [0,1], using two independent iid samples (labeled n, unlabeled N) from the same distribution, a fixed scalar score S=f(X). Real-data evaluation uses the empirical paired distribution with sampling WITH replacement and disjoint labeled/unlabeled RNG draws; mu is its full observed label average, evaluation-only. Within a replicate all methods get identical rows, labels and frozen scores. This is not conditional coverage given a realized dataset.

## Narrow contribution and anticipated rejection
Not a claim to invent nonlinear control variates, calibration, cross-fitting, or empirical Bernstein bounds. Derive/validate the exact oracle score-only variance gap beyond optimal scalar PPI++; audit how its theoretical savings survive finite n and rigorous finite-sample protection. Main likely rejection: standard ideas/limited novelty; acknowledge rather than claim priority. Other risks: asymptotic coverage mistaken for exact; learned predictor violates fixed constraint; real-data empirical distribution not original scientific population; selection affects coverage; no universal shrinkage.

## Stage 1: inputs and baseline verification
Read only allowlisted original starter URLs; acquire official ICML2026 template and author instructions directly. Main body <=8 pages, impact statement; inspect template for checklist requirements. Download galaxies/forest (frozen predictions), synthetic always available. Verify PPI++ formula against original mean formula and ppi-python 0.2.3 when feasible. Tests for estimator invariance, analytic variance identity, empirical-Bernstein edge cases, paired data integrity.
Artifacts: literature/*, data/*, template/*, tests/, provenance.

## Stage 2: fixed inference recipes (no outcome-based hyperparameter search)
Asymptotic: classical Wald; PPI lambda1; PPI++ unrestricted lambda using pooled prediction variance; CF scalar; CF nonlinear polynomial/hinge basis; unsafe in-sample high-dimensional fit as a negative control (clearly not valid baseline). Crossfit 5 folds, fixed ridge 1e-6 of sample Gram scale; fixed basis score polynomials through degree3 plus hinge at .25,.5,.75 and indicator score>.5 (p=7). Compare simpler polynomial basis and split-only as ablations if feasible.
Finite sample: exact binomial Clopper-Pearson for binary labels; known-range empirical-Bernstein labeled; EB PPI fixed score; EB finite dictionary of predeclared maps, selecting minimum-width interval with simultaneous confidence correction. No learned map in this bound. Formula checked in original 2009 empirical-Bernstein reference. Include naive uncorrected selection only if needed and mark unsafe.

## Stage 3: paired evaluation
Synthetic mechanisms with S~Uniform[0,1], Y~Bernoulli(m(S)): linear m=.1+.8S; quadratic m=.05+.9(2S-1)^2; step m=.05+.9 1{S>.5}; null m=.5; rare m=.01. Values fixed. n in {100,500}, N=10n; all 5 scenarios, 2000 repetitions per cell, seeds 20261102+ independent SeedSequence cell streams. Extra n=30 and N/n in {1,100} for linear/quadratic/rare stress if resources permit. Oracle mu and variance integrated analytically. Primary metrics: marginal coverage (Wilson 95% intervals), average width (MC SE), paired mean-width ratio vs PPI++ with delta-method SE, and relative ratio of estimated errors. Report all cells; no cherry picking. 95% nominal intervals. Coverage is descriptive; no automatic declaration of validity from a Wilson interval. Holm adjustment for any explicit many-cell hypothesis tests.
Real galaxies/forest: n in {100,500}, N=10n, 2000 iid with-replacement resamples from fixed finite empirical joint distribution. Original labels accessed only by simulation/evaluator; fitting functions receive ONLY current labeled data and score arrays. Download failure disclosed, no substitute invented.
Plots: efficiency/coverage panels, width vs guarantee tradeoff. Tables: full machine-readable all methods/cells plus concise paper tables.

## Stage 4: theoretical and empirical audit
Prove V(g) completing square for all square-integrable deterministic score functions; characterize equality and attainable gap against scalar controls. No global optimality claim across arbitrary X/parametric assumptions. Finite dictionary union-bound proof with known outcome/score ranges. Independent audit of clean theorem. Failure cases and non-dominance explicitly stated. Baseline reflection after smoke run; no method changes based on confirmatory runs. Any additional analyses labeled exploratory.

## Stage 5: paper and reproduction
Use unmodified ICML2026 official style, final <=8 body pages; references/appendices separate. English research paper plus Chinese summary. Every numeric value generated from results CSV via table script; no placeholders. Pin dependencies; preserve seeds, exact commands, data hashes, environment, timings, figures scripts. Compile PDF, verify page/body boundaries, tests, artifact existence, source-access log, independent reject-first review and fixes. Save final_report.md, README.md, paper.tex/paper.pdf, all code at workspace root or subdirectories under it.
