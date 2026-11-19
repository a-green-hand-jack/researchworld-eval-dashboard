# Analytic results for the OLS(z, f) estimator (linear-exposure family)

Setting. Graph with row-normalised adjacency W (f = W z is the neighbour treated fraction), degrees d_i, harmonic mean degree
d_H = (mean_i 1/d_i)^-1. Bernoulli(p) assignment z. Observed y = b + τ z + g(f) + e where b is a *fixed* baseline vector
(centred below), e is fresh noise with variance σ_e², and the target is GATE = τ + g(1) − g(0). The estimator fits OLS
y ~ 1 + z + f and returns GATĒ = β̂_z + β̂_f (prediction at z=1,f=1 minus z=0,f=0).

**Status of statements.** Both results below are first-order (large-n, linearisation) derivations, verified numerically
(`code/scripts/theory_check.py`), not rigorous finite-sample theorems; "proved" is NOT claimed.

## P1 (bias under a non-linear exposure response) — population, noise-free
Because z_i is independent of f_i, Cov(z, f)=0 and the pooled population slope on f is
β_f* = Cov(g(f), f) / Var(f), with f_i | d_i ~ Bin(d_i, p)/d_i and moments averaged over the degree distribution.
Hence plim(GATE-hat) − GATE = β_f* − [g(1) − g(0)]  (the z-coefficient recovers τ exactly).
Consequences: (i) linear g ⇒ zero bias for every graph/p; (ii) for smooth g and large degree, f concentrates at p and
β_f* → g′(p): the bias tends to the *tangent-vs-secant gap* g′(p) − [g(1) − g(0)], which does not shrink with n; it is
nonzero in general and vanishes only at special points (e.g. g(f)=f² at p=1/2); (iii) low degree spreads f over [0,1]
and moves β_f* toward the secant slope, so sparser graphs extrapolate better. Implemented as `netgate.theory.pop_bias_ols_f`.

## P2 (variance, correct specification)
With centred fixed baseline b, the OLS error linearises to Σ⁻¹ n⁻¹ Σ_i x̃_i ε_i with Σ = p(1−p)·diag(1, 1/d_H) (z and f are
uncorrelated). Writing GATĒ − GATE ≈ [p(1−p) n]⁻¹ (z − p)ᵀ (ε + d_H Wᵀ ε), and using independence of the z_k,

  Var(GATĒ) ≈ [ ‖b + d_H Wᵀ b‖² / n + σ_e² (1 + d_H) ] / ( n p (1−p) ).

Reading: (a) the error is *design-based*: it comes from how the fixed baseline projects on the random exposures, not only
from "noise"; (b) the noise part grows linearly in d_H (a unit with many neighbours has an almost constant f, so the
coefficient on f is poorly identified from n units — error SD ∝ √(d_H/n)); (c) if baselines are smooth over the graph
(homophily; Wᵀ b ≈ b), the baseline part grows like d_H² so the SD grows ∝ d_H, much faster than for white-noise baselines
(for which ‖b + d_H Wᵀb‖² ≈ ‖b‖²(1 + d_H)); (d) the dependence on p is 1/√(p(1−p)): small p is costlier.
Implemented as `netgate.sim.theory_sd`; it does not depend on the interference strength γ or on τ, which matches the
simulations (the absolute error is flat in γ; only the relative error falls).

## P3 (bias when the signal is linear in z but not linear in f alone)
If m_i(z) = τ z_i + Σ_j M_ij z_j (e.g. heterogeneous γ_i, a 2-hop term, a count-scaled exposure), then under Bernoulli(p) the
population OLS limit is slope_z = τ + mean_i M_ii and slope_f = Σ_ij W_ij M_ij / Σ_ij W_ij² (p cancels). Reading:
for M = diag(γ) W the f-slope is a *1/d_i-weighted* average of γ_i (Σ γ_i/d_i / Σ 1/d_i), whereas the GATE weights units equally:
the regression estimator is biased whenever the spill-over strength correlates with degree, because low-degree units
dominate the identification of the f-coefficient; for a 2-hop term the f-slope absorbs only the part of W² that
overlaps W (a function of clustering). Implemented as `netgate.theory.pop_plim_linear`; checked in `code/scripts/theory_check.py`.
These limits are for the *noise-free, baseline-free* fit (`ols_f@pop` in the results), which isolates the approximation error from finite-sample noise.
