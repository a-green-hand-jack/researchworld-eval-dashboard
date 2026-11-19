# Self-contained methods for the report owner

## Response target, generator and splits

Y is an observed response composition, not an unobserved class-probability vector or a discrete class label. Let K be 3 or 10, G~Bernoulli(.2), and Z=(Z1,Z2,Z3) iid N(0,1), independent of G. X=(G,Z). The design row is phi(X)=(1,G,Z1,Z2,Z3,Z1*Z2,Z1^2), with seven columns. For each K, draw a 7xK coefficient matrix with independent N(0,.32^2) entries using NumPy RNG seed 1729+K, then center each row over its K coordinates. This one coefficient matrix is fixed across replications; the study does not average over coefficient draws.

Write a_j as K equally spaced values between .65 and 1.35, divided by sqrt(mean_j a_j^2). Generate independent E_j~N(0,1) and logits L=phi(X)B+sigma(X)*(a_1 E_1,...,a_K E_K); Y=softmax(L). Homogeneous sigma=.45. Heterogeneous sigma=(.18 if G=0 else .95)*exp(.15 Z1). Anisotropy is fixed, and the softmax implies a logistic-normal distribution on the positive simplex. Each replication draws 1000 training, ncal calibration and 5000 iid test points independently. The shift evaluation independently draws 5000 points with G~Bernoulli(.8) while preserving the entire within-group joint law of (Z,Y). The trained model and thresholds are shared between evaluation environments, except oracle weighting explicitly knows the target environment.

Main seeds are 901000..901099, reused across methods within a cell. Corresponding cells may reuse random seeds; they are not pooled as independent replications. Dimensions, noise settings and calibration sizes are separate estimands. The source hash and exact library versions are stored in each raw-file manifest. No external data are used. Pilot seeds 900000/900001 are excluded.

## Fitted point and scale models

clr(y)_j=log(y_j)-K^{-1}sum_l log(y_l). Fit ridge coefficients C=(Phi'Phi+R)^{-1}Phi'clr(Y_train), with R diagonal 1e-3 except an unpenalized intercept. Predict p(x)=softmax(phi(x)C). This is a fitted clr center, generally not the conditional arithmetic mean of Y. The synthetic mean-logit function lies in the fitted basis, which favors this simple log-ratio model and limits external generalization.

On training observations only, compute residuals r_i=clr(Y_i)-phi(X_i)C and t_i=log(max(||r_i||_2^2,1e-12)). Regress t on the same phi by the same ridge formula, yielding d. The adaptive scale is s(x)=exp(clip(phi(x)d/2,-12,12)). Calibration/test data never fit or choose C, d or tuning parameters. In-sample training residuals may bias scale level; the conformal threshold absorbs any constant multiplicative scale error, but shape errors may remain. There is no oracle noise scale supplied to this method.

## Scores and calibration

At alpha=.1, calibrate an ordinary scalar score using the kth calibration order statistic, k=ceil((ncal+1)(1-alpha)); if k>ncal use infinity. Include score ties via the non-strict test S<=q (conservative). Regions are intersected with the simplex; finite clr-score regions have positive-simplex domain. Infinity is the explicit whole-simplex fallback.

- raw_l2: ||y-p(x)||_2.
- raw_linf: max_j |y_j-p_j(x)|.
- clr_l2: ||clr(y)-clr(p(x))||_2 (Aitchison distance; identical to orthonormal ilr distance).
- clr_scaled: the clr_l2 score divided by training-estimated s(x).
- clr_mondrian: clr_l2 score, but a separate rank threshold is calibrated within each predeclared observed group. Empty or too-small groups get infinity. G is known at prediction.
- coord_naive: each absolute coordinate residual calibrated at alpha; require every coordinate to meet its threshold. This is a negative control without the joint 1-alpha guarantee.
- coord_bonferroni: each absolute coordinate residual calibrated at alpha/K; require all coordinates, giving the union-bound joint guarantee.
- clr_weighted: clr_l2 with oracle ratio weights 4 for G=1 and .25 for G=0 under shift; unit weights under iid. At a test x, find the first calibration score whose cumulative weight reaches (1-alpha)*(sum calibration weights+w(x)), otherwise infinity. This implements a test-weight atom at infinity. It uses known generator information and guarantees shifted marginal coverage under the stated within-group-preserving covariate shift, without a general subgroup guarantee.

For scalar-score methods the standard rank coverage is marginal over calibration and test, conditional on the independently trained predictor. It is not a promise for each realized calibration set or x. Bonferroni is conservative. Group calibration is group-valid conditional on the group's calibration count under within-group exchangeability. The oracle weighted construction was checked directly against the permitted starter paper arXiv:1904.06019, Section 2.1 Corollary 1 and equations (7)-(10), read 2026-11-02; direct PDF hash d80dba944a136e075bbfe281009152ce42041e0a455f68f73684ace83cfc3fed. No broader search or prohibited publication was accessed by this position.

## Coverage, chosen area reference and uncertainty

Coverage is the fraction of entire test response vectors inside each region; also report both group fractions with group counts. At K=3, draw 32 new independent X anchors from each environment and 8192 independent uniform Dirichlet(1,1,1) candidates per anchor. The mean membership estimates the fraction of Euclidean simplex area. Candidates are shared across methods, making area contrasts paired. This is a chosen reference measure, not a measure-free utility ordering or clr volume. No cross-geometry K=10 efficiency ordering is supplied.

For anchor hit fraction v_a and M candidates, candidate-only Monte Carlo SE conditional on anchors/regions is sqrt(mean_a[v_a(1-v_a)]/(A*M)); the recorded value is not the uncertainty across anchors, trained models or calibration datasets. Independent-replication t intervals encompass all these sources. Volume zero hits are unresolved small fractions, not proof of zero area. Claims of a close area ordering require a higher-candidate paired check or will be withheld.

Summaries use R independent dataset estimates, mean +/- t_{.975,R-1}*sampleSD/sqrt(R). Method contrasts are differences within the same replication; environment contrasts are shifted minus iid within the same trained/calibrated run. Pointwise 95% intervals are descriptive, not simultaneous and not equivalence tests. Keep achieved precision visible. The distribution of finite-test coverage estimates (SD and 10/50/90 percentiles) and fraction below nominal minus .05 diagnose calibration variation, with a Wilson interval across R independent indicators for that empirical tail fraction. Finite-test noise remains; these are not exact probabilities of conditional population coverage. Test observations are not counted as independent calibration replications.

Infinity is never dropped from coverage or area. Every raw row records group calibration counts, infinite-threshold status and infinite-radius fraction. If any radius in a cell is nonfinite, its complete-cell mean/CI is omitted, with finite and total denominator and explicit status. Radii have method-specific units and never establish cross-geometry efficiency.

## Boundary scope checks

For focused sensitivity only, censor components below .025 to exactly zero and reclose. T_epsilon(y)_j=max(y_j,epsilon)/sum_l max(y_l,epsilon), with epsilon={1e-8,1e-4,1e-2}; use identical original datasets across epsilon. At K={3,10}, ncal499, alpha .1, 50 fresh seeds 902000..902049 and 5000 iid test points, train the center/scale on transformed training responses. Raw original-target scores calibrate/evaluate original censored Y; transformed scores consistently calibrate/evaluate T_epsilon(Y). A separately labeled original-target clr diagnostic uses the transformed-calibrated set and rejects any original boundary response for finite clr regions. Infinity means the whole simplex. A direct untransformed clr ball cannot establish boundary-response coverage from transformed results alone; the pullback below can supply original-target coverage under exchangeability; censoring is one chosen measurement mechanism and is not a model for all zero types. The study does not claim robustness to arbitrary covariate shift, unknown groups/ratios, other coefficient draws, or real applications.


## Source-driven score controls (protocol v1.2)

Two matched-seed score controls were added after the core/oracle results were available to analysis, because the context owner identified them in permitted starter prior work (Javanmardi et al.). They are score controls under our shared fitted clr center, not a reproduction of that prior work's entire pipeline. All main cells/seeds/area candidates are reused, output separately in `results/prior_scores.jsonl`, then combined into ten-method summaries. The original core remains unchanged.

TV is half the sum of absolute coordinate residuals. On K=3 it equals raw maximum residual exactly on the simplex: total positive and negative residual masses agree, and at least one side has at most one component. The implementation uses that equality to canonicalize the duplicate at K3, avoiding sub-ULP discrepancies; formula equality and exact measured memberships/areas are checked. K10 TV is a distinct score. Forward KL is sum_j y_j log(y_j/p_j), evaluated with scipy.special.xlogy as sum(xlogy(y,y)-xlogy(y,p)), clipped only against tiny negative rounding error. Fitted p is positive. The orientation is y||p; 0log0 terms are zero. Checks cover nonnegativity, identity, asymmetry and the analytic KL((0,1)||(1/2,1/2))=log2. Both scores receive ordinary joint finite-rank calibration and have the same iid marginal guarantee as the other fixed joint scores, but no general subgroup or unweighted-shift guarantee. All paired contrasts against raw L2/max and Aitchison are retained. No novelty claim of the first compositional conformal region is supported.


## Original-target pullback of the replacement region

For the fixed deterministic clipping-and-reclosure transform T_epsilon used here, define C_pre(x)={y in the original simplex:T_epsilon(y) in C_epsilon(x)}. Then the indicator of Y in C_pre(X) equals the measured indicator of T_epsilon(Y) in C_epsilon(X), observation by observation. Thus the transformed coverage guarantee and every measured transformed coverage/CI also apply to this explicitly defined original-target region, including its boundary. Invertibility is unnecessary. `results/boundary_summary/pullback_equivalence.csv` reports this exact reinterpretation of already measured events, with explicit provenance; it is not an additional independent experiment. The direct-clr diagnostic is a different region and must not be used to claim all replacement-based conformal methods fail at zeros. Clipping may collapse distinct original compositions into the same transformed outcome and change region shape/utility. We did not estimate original-simplex area for this pullback, so cannot assert its efficiency. This clarification follows the context Brief's distinction; no outcome was discarded.
