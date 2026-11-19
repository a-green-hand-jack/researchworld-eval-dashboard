# Asymptotic width theory (assumptions, statement, scope)

**Setting.** (Y_i, f_i), i=1..n iid; f_j, j=1..N iid from the same law of f (labeled/unlabeled exchangeable; f = fixed
predictor output, Y_i independent of unlabeled data); n,N → ∞ with ω := N/(n+N) ∈ (0,1) fixed; target θ = E[Y];
σ² = Var Y, g(f) = E[Y|f], ρ² = corr(Y,f)², R²_cal := Var g(f)/σ² ≥ ρ² (equality iff g is affine).
Information used: labeled (Y,f) and unlabeled f. No new labels, predictor or unlabeled points.

**Class.** θ̂_φ = mean_lab(Y − φ(f)) + mean_unl φ(f) for a fixed (data-independent) φ. Unbiased for every φ;
√n-asymptotic variance V(φ) = Var(Y−φ)/n + Var(φ)/N (the CI is Wald with the plug-in V̂).

1. *PPI* φ=f; *PPI++* φ=λf (λ tuned, optimum λ* = Cov(Y,f)/((1+n/N)Var f)): V_PPI++ = σ²(1 − ω ρ²)/n.
   (PPI++ with λ unrestricted; the package clips λ̂ to [0,1], which is suboptimal whenever the slope of Y on f exceeds 1+n/N·… i.e. λ*>1.)
2. *Optimal φ.* Var(Y−φ) = E Var(Y|f) + Var(g−φ), so V(φ) = E Var(Y|f)/n + Var(g−φ)/n + Var(φ)/N, minimised by
   φ* = ω g (+const), giving **V* = E[Var(Y|f)]/n + Var g/(n+N) = σ²(1 − ω R²_cal)/n.**
3. Hence asymptotic width ratio (optimal / PPI++) = sqrt((1 − ω R²_cal)/(1 − ω ρ²)) ≤ 1, equality iff g affine in f
   (or ω→0). Gain is bounded by the nonlinearity R²_cal − ρ² and vanishes as ω→0 (few unlabeled points); largest at ω→1.
4. V* is the semiparametric efficiency bound for estimating E[Y] from (labeled (Y,f), unlabeled f) under MCAR labeling when only f
   is used (standard AIPW/efficient-influence-function calculation; stated, not re-derived here); so with f the only information,
   **no regular estimator, hence no asymptotically valid Wald-type interval, is shorter than sqrt(V*)·z**. Adding covariates X
   can only lower the floor to E Var(Y|f,X)/n + …; on census_* we measure no such headroom (see README).
5. *Plug-in cost.* g must be learned from the n labels; cross-fitting keeps the interval valid but pays an O(df/n) relative
   variance inflation (df = effective dimension of the calibration map): observed 0.5–2 % at n≥400 for spline/isotonic,
   up to 5–20 % at n≤100 (results/theory_check_synth.csv, summary_*.csv).

**Not covered by the theory.** Finite-n coverage (all intervals are CLT-based; rare binary Y, tiny residual variance, heavy tails
undercover at n ≲ 100–200, see simulation), covariate shift between labeled and unlabeled (PPI-type estimators are then biased;
PPI++ power tuning with labeled-only covariance can make it worse, plankton), non-mean targets.
