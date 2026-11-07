# Implementation decisions frozen before confirmatory runs

- Fixed rich basis is p=4: S, (2S-1)^2, (2S-1)^3, 1{S>.5}; simpler poly2 basis is first2, scalar first1. The originally proposed p=7 hinge expansion is not pursued: p=4 already contains both nonlinear synthetic conditional means and avoids redundant features. This decision precedes simulation results.
- Ridge epsilon_n=1e-4/n (not a fixed epsilon) to match theorem conditions. Folds are deterministic index-mod5 on iid row order, independent of values. All folds use exact n_k/n weights, and unlabeled variance is of the average fold control, retaining its covariances.
- Add a separate `ppipp_pkg` baseline: ppi-python0.2.3 clips lambda to[0,1], uses biased label covariance and ddof0 residual/unlabeled variances. `ppipp` remains the stronger unrestricted original-paper mean recipe, using pooled score variance. These must not be conflated.
- Intersect every interval with[0,1]. A wholly disjoint raw interval is collapsed to its nearest endpoint (can only alter failure events). Record both reported and untruncated widths.
- Finite-safe dictionary has K=5:0,aS,a(1-S),a(2S-1)^2,a1{S>.5}, a=1/(1+n/N). Zero control gets alpha/K; other controls split alpha/(2K) per component. Selection by truncated interval width; fixed tie order.
- Step signal strengthened to m=.01+.98 indicator(S>.5); quadratic m=.02+.96(2S-1)^2. These analytic mechanisms are fixed before experiments. Binary outcomes are explicitly Bernoulli conditionally on S.
- Core grid n={100,500,2000}, N/n=10, 2000 reps per cell across5 synthetic and2 empirical distributions. Stress grid n30,N/n10 for all5 synthetic; n500,N/n1 or100 for linear/quadratic/rare. Resource-dependent smaller stress grids will be disclosed if not completed.
- Crossfit nonlinearity does not claim exact finite-sample coverage. EB methods and CP have analytical nonasymptotic validity; compare these in a separate validity tier. A poor finite-safe width result is an acceptable outcome.

## Theory audit repairs before runs
External clean-proof audit required observation-independent folds, correct ridge coefficient rate O_p(n^-1/2+epsilon_n), and explicit Bernoulli outcomes for variance formulas. All repaired above. Oracle identity and finite dictionary validity were accepted. See artifacts/theory_audit.md for proofs and counterexample to a broader score-sorted-fold interpretation.
