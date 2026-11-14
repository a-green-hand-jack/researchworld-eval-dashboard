# Allowlisted original sources: mean inference and post-processing

## Scope, provenance, and reading status

Research date: **2026-11-02 UTC**. Only the following five external URLs were accessed, directly, with redirects disabled. No abstract pages, external searches, citation links, code repositories, datasets, recommendations, or other articles were accessed. References appearing inside these originals were not followed. No identifiable prohibited material was encountered; no incident log was triggered. The prohibited paper is unidentified, so unknown overlap cannot be certified absent.

| ID | Title verified in downloaded original | Exact URL accessed | Access time UTC | PDF pages |
|---|---|---|---|---|
| [1] | Prediction-Powered Inference — Angelopoulos, Bates, Fannjiang, Jordan, Zrnic | https://arxiv.org/pdf/2301.09633 | 2026-11-02 18:05:14.524379 | 40 |
| [2] | PPI++: Efficient Prediction-Powered Inference — Angelopoulos, Duchi, Zrnic | https://arxiv.org/pdf/2311.01453 | 2026-11-02 18:05:18.323110 | 29 |
| [3] | Cross-Prediction-Powered Inference — Zrnic, Candès | https://arxiv.org/pdf/2309.16598 | 2026-11-02 18:05:21.932009 | 29 |
| [4] | Stratified Prediction-Powered Inference for Hybrid Language Model Evaluation — Fisch, Maynez, Hofer, Dhingra, Globerson, Cohen | https://arxiv.org/pdf/2406.04291 | 2026-11-02 18:05:26.316082 | 20 |
| [5] | Double/Debiased Machine Learning for Treatment and Structural Parameters — Chernozhukov et al. | https://arxiv.org/pdf/1608.00060 | 2026-11-02 18:05:30.021237 | 71 |

Full HTTP metadata, byte counts, and SHA-256 hashes: `access_log.jsonl`. These were **unversioned URLs**: claims here concern the actual PDFs downloaded on this date, not necessarily their first arXiv versions. No version number is inferred.

Downloaded files: `<arxiv-id>.pdf`. Local standard-library-only extraction: `<arxiv-id>.txt`; whitespace-reflowed reading copies: `<arxiv-id>.wrapped.txt`. Extraction helper: `extract_local.py` (document processing only; **no statistical method implementation**). PDF page boundaries are retained. Mathematical layout/superscripts are linearized, so equations below are manually reconstructed from the extracted original text, not copied blindly from reflowed lines. Page references below are PDF page numbers (the printed numbers agree in the sections cited).

Read substantively: [1] pp. 1–7, 23–27, 32–34 (plus nearby proof material); [2] pp. 1–14; [3] pp. 1–12; [4] pp. 1–9; [5] pp. 1–7, 11–13, 22–29. No claim of reading all five papers in full.

## Notation and shared assumptions

Let `S=f(X)`, let `bar S_U=N^{-1} sum_i f(tilde X_i)`, and let `bar S_L=n^{-1} sum_i f(X_i)`; `bar Y_L=n^{-1} sum_i Y_i`. The labeled and unlabeled samples are independent i.i.d. samples with the same feature marginal. Original PPI assumes `f` is independent of the inference data, e.g. trained separately [1, §1.2, p. 3]. An arbitrary fixed black box need not consistently estimate a conditional expectation to obtain validity. This is not permission for inference-data leakage or arbitrary distribution shift.

For exact empirical-variance conventions, write

`vhat_m(A)=m^{-1} sum_i (A_i-bar A)^2`,

and similarly use centered empirical covariance. The denominator-`m` convention is explicit in [1, Algorithm 1, p. 7]. The PPI++ algorithms use empirical covariance notation; replacing a denominator by `m-1` is asymptotically equivalent, but is not the exact displayed convention of [1].

## 1. Original PPI: estimator, variance, and interval

**Source:** [1], §1.3 p. 3; §2.1/Proposition 1 p. 6; Algorithm 1 p. 7.

For `mu=E[Y]`, define

`Delta_hat = n^{-1} sum_i (S_i-Y_i)`,

`mu_hat_PPI = bar S_U - Delta_hat = bar Y_L + bar S_U - bar S_L`.

This estimator is unbiased for a fixed independent predictor under the common-distribution setup. Its two displayed summands are independent. The exact fixed-predictor sampling variance, by independence, is

`Var(mu_hat_PPI)=Var(Y-S)/n + Var(S)/N`.

Algorithm 1 explicitly computes

`vhat_f = N^{-1} sum_i (f(tilde X_i)-bar S_U)^2`,

`vhat_f-Y = n^{-1} sum_i (S_i-Y_i-Delta_hat)^2`,

and returns

`C_PPI = mu_hat_PPI ± z_(1-alpha/2) sqrt(vhat_f-Y/n + vhat_f/N)`.

**Guarantee:** Proposition 1 states `liminf_{n,N→infinity} P(mu in C_PPI) >= 1-alpha`, not finite-sample exact normal coverage. Appendix C.3 p. 27 requires finite first two moments of the relevant gradients/rectifiers; for means these are `S` and `S-Y`. The formal general asymptotic theorem C.1, p. 25, assumes `n/N→p in (0,1)`; do not silently replace its stated ratio condition by every imaginable unequal-rate regime. PPI++ separately permits a limiting ratio zero under its regularity conditions.

**Failure mode:** Original PPI with weight 1 need not improve on the labeled mean. By the variance identity it improves iff

`(1+n/N) Var(S) < 2 Cov(Y,S)`

(strict inequality, nondegenerate comparison). This condition is an algebraic consequence of Algorithm 1, not a separately numbered result. Small residual variance, not merely small mean bias, is what matters for width. A constant additive bias cancels exactly in the estimator.

### Finite-sample PPI is a separate construction

**Source:** [1], Theorem 1 p. 5; Appendix C.2 pp. 25–27, Algorithm 10/Corollary C.1 p. 26; Appendix E.1 pp. 32–33.

For `0<delta<alpha`, use valid mean confidence intervals

`[a_L,a_U]` for `E[S]`, at error `alpha-delta`, from the unlabeled predictions;

`[d_L,d_U]` for `E[S-Y]`, at error `delta`, from the labeled residuals.

Then

`C_finite = [a_L-d_U, a_U-d_L]`,

with `P(mu in C_finite)>=1-alpha` by the theorem/union bound. Endpoint notation here is not intended to change the paper's open-interval convention.

Algorithm 10 assumes **known almost-sure bounds** `Y,S in [0,B]`, and supplies MeanCI with ranges `[0,B]` and `[-B,B]`, respectively. It is not the Wald interval above. The paper's default MeanCI is a variance-adaptive betting construction, not a Gaussian interval.

For completeness, Proposition E.1's ideal continuous-set construction, after normalizing observations `Z_t` to `[0,1]`, is:

`mu_hat_t=(0.5+sum_{j<=t} Z_j)/(t+1)`,

`sigma_hat_t^2=(0.25+sum_{j<=t}(Z_j-mu_hat_t)^2)/(t+1)`,

`lambda_t=sqrt(2 log(2/alpha)/(n sigma_hat_(t-1)^2))`.

For candidate `m`, define

`P_t^+(m)=prod_{j<=t} [1+min(lambda_j,0.5/m)(Z_j-m)]`,

`P_t^-(m)=prod_{j<=t} [1-min(lambda_j,0.5/(1-m))(Z_j-m)]`,

`M_t(m)=0.5 max(P_t^+(m),P_t^-(m))`.

It reports `C=intersection_{t=1}^n {m in [0,1]: M_t(m)<1/alpha}` and `P(E[Z] in C)>=1-alpha`; map the result back to the original known range. Quotients at endpoints are interpreted by their limiting/truncation convention. The paper calls `M_t` a supermartingale; the notes only reproduce the rejection construction and stated coverage, not an independently verified assertion that the maximum itself is a supermartingale. Algorithm 13 uses a numerical grid: a bare discrete grid cannot literally cover an arbitrary real mean without an enclosure convention. The exact coverage statement should be attached to the continuous-set theoretical construction, not assumed to hold automatically for arbitrary numerical gridding.

### Finite population is different from finite sample

[1], Appendix B/Corollary B.1 pp. 23–24: all `N` population features/predictions are known and `n` labels are sampled uniformly **without replacement**. Target is the finite-population outcome mean, not a superpopulation expectation. If `[R_L,R_U]` covers the finite-population mean residual `N^{-1}sum_i(S_i-Y_i)`, then the interval is `[bar S_population-R_U,bar S_population-R_L]`. There is no separate sampling uncertainty for a prediction average over the whole fixed population. Appendix E.4 p. 34 gives a CLT interval with finite-population correction `sqrt((N-n)/N)`; E.3 p. 33 supplies a separate bounded-data nonasymptotic construction. Do not mix this design with the independent two-sample variance formula.

## 2. PPI++: scalar tuning, exact range, and estimated uncertainty

**Source:** [2], weighted objective `(P_lambda)` p. 4; Theorem 1/Algorithm 2 p. 8; Proposition 2 p. 10; plug-in (8) and range discussion p. 11; Example 6.1 p. 12.

For a fixed real `lambda`, the mean estimator is

`mu_hat_lambda = bar Y_L + lambda (bar S_U-bar S_L)`.

It remains unbiased for fixed `lambda`, and its **exact fixed-weight variance** is

`Var(mu_hat_lambda) = Var(Y-lambda S)/n + lambda^2 Var(S)/N`.

Writing `r=n/N` for the finite-design calculation (or its limit for asymptotic variance), define

`V(lambda)=Var(Y)-2 lambda Cov(Y,S)+(1+r)lambda^2 Var(S)`.

For `Var(S)>0`, the unique unconstrained optimizer is

`lambda_star=Cov(Y,S)/[(1+r)Var(S)]`.

This is explicitly Example 6.1, not a new tuning formula. Its corresponding variance reduction, by substitution, is

`V(lambda_star)=Var(Y)-Cov(Y,S)^2/[(1+r)Var(S)]`

`=Var(Y)[1-Corr(Y,S)^2/(1+r)]`

(the correlation representation requires positive outcome variance). Divide by `n` for estimator variance. The oracle improves on both fixed choices `lambda=0` and `lambda=1` because both belong to the optimization domain. This does **not** mean every realized plug-in interval is narrower or has finite-sample nominal coverage.

**Admissible range:** For **mean estimation, all real lambda are allowed**, and the objective is always convex [2, Example 6.1 p. 12]. Negative correlation can yield negative `lambda_star`; an under-scaled predictor can yield `lambda_star>1`. The interval `[0,1]` is a sufficient convexity region for general GLM rectified objectives, not a universal statistical requirement. For those other losses, p. 11 discusses clipping or a one-step estimator. If a mean method is intentionally constrained to `[0,1]`, its oracle is the projection of the displayed `lambda_star` onto `[0,1]` (our quadratic-optimization consequence). A constant predictor gives no correction; the ratio is undefined and one should revert to the labeled mean, rather than divide by zero.

**Exact displayed mean plug-in tuning:** Example 6.1 uses

`lambda_hat = Covhat_L(Y,S)/[(1+n/N) vhat_(N+n)(S)]`.

The numerator is labeled-sample empirical covariance; the denominator uses predictions from labeled and unlabeled data **pooled together**. This is not a formula with an unlabeled-only denominator in the displayed example.

**Variance estimate/CI from Algorithm 2 specialized to means:**

`Sigma_hat = (n/N) lambda_hat^2 vhat_(N+n)(S) + vhat_n(Y-lambda_hat S)`,

`C_PP++ = mu_hat_(lambda_hat) ± z_(1-alpha/2) sqrt(Sigma_hat/n)`.

Mean loss has Hessian 1 (using half squared loss). Using an unlabeled-only estimate for prediction variance is another consistent choice under the model, but is not this algorithm's exact pooled convention. Original PPI uses unlabeled-only prediction variance.

**Guarantee/assumptions:** Theorem 1 assumes `lambda_hat→p lambda`, `n/N→r>=0`, smooth-enough losses, and consistency of the optimizer; covariance/Hessian regularity supplies the usual sandwich CLT. Mean estimation reduces to moment and nondegeneracy requirements. Corollary 3 gives asymptotically correct coordinate coverage; Corollary 4 p. 11 gives the oracle-limit CLT for consistent power tuning. A data-dependent weight is not the same as a fixed weight: do not claim exact finite-sample unbiasedness or substitute it into the fixed-weight exact variance as an identity. Tuning uncertainty is negligible to first order under the stated consistency theorem; this is not a finite-sample guarantee.

**Already-discussed relationship:** [2], Eq. (4) pp. 4–5, rewrites the mean AIPW estimator using both labeled and unlabeled predictions as the same family with `lambda=1/(1+r)`. This is especially relevant when `f(X)=E[Y|X]`, but is not the arbitrary-predictor optimal scalar weight in general. Only this relationship as stated in [2] is cited; none of its references was accessed.

## 3. Nonlinear post-processing: what follows, and what does not

**Attribution boundary:** The following identities/optimizations are **our algebraic consequences** of [1]'s arbitrary fixed-predictor setup and [2]'s Example 6.1, not separately claimed theorems found in the five originals. A keyword check found no relevant explicit discussion headed 'nonlinear' in the read PPI/PPI++ material. No outside post-processing paper was searched for or inferred.

### Fixed transformation of predictions

For a fixed measurable transformation `g` with finite required moments, set `T=g(S)=g(f(X))`. It is just another predictor in the original framework:

`mu_hat_(lambda,g)=bar Y_L+lambda(bar T_U-bar T_L)`,

`V(lambda,g)=Var(Y-lambda T)+r lambda^2 Var(T)`.

For nonconstant `T`,

`lambda_star(g)=Cov(Y,T)/[(1+r)Var(T)]`,

`V_star(g)=Var(Y)-Cov(Y,T)^2/[(1+r)Var(T)]`.

Thus nonlinear post-processing can change the obtainable reduction through its correlation with `Y`; mere recalibration is not a validity requirement, and a nonlinear map is not guaranteed to improve efficiency. It is generally **not** equivalent to changing a scalar weight on the raw scores.

For an affine map `g(s)=a s+b`, `a!=0`, the constant cancels in the two-sample difference and `lambda_star(g)=lambda_star(raw)/a`. Consequently the **unconstrained oracle-tuned estimator and variance are affine-invariant**. With weight constraints, the corresponding feasible effective weights can differ. With constant `g`, the correction is zero. These are algebraic identities, not new source claims.

### Oracle nonlinear map when only the score S is available

Let `m(S)=E[Y|S]`. Absorb the scalar into a correction `h(S)` and consider `bar Y_L+bar h_U-bar h_L`. Conditional expectation gives

`V(h)=Var(Y-h(S))+r Var(h(S))`

`=Var(Y)-Var(m(S))/(1+r)+(1+r)Var(h(S)-m(S)/(1+r))`.

Therefore the oracle is `h_star(S)=m(S)/(1+r)+c`, with minimized value

`V_oracle=Var(Y)-Var(E[Y|S])/(1+r)`.

Equivalently, use predictor `m(S)` and scalar `1/(1+r)`. This is an oracle projection calculation, **not an estimator, validity theorem for a learned map, or a novelty finding**. It exploits only information in `S`, not necessarily all information in `X`. Nonlinear improvement beyond unrestricted scalar tuning is possible when the conditional mean cannot be represented by an affine function of `S` (nondegenerate case); affine conditional means yield the same oracle reduction as scalar tuning.

### Limitations and leakage

- Learning `g` on the same labels used for rectification breaks the independent-fixed-predictor premise. The scalar plug-in tuning result in [2] does not alone justify a high-dimensional/nonparametric learned map.
- Independent calibration data restores the fixed-predictor setup conditional on the fitted map. Cross-fitting instead needs a theorem with appropriate stability/rate assumptions; simply calling a procedure cross-fitted is not enough [3], [5].
- No calibration assumption is needed for validity of fixed-predictor PPI, but calibration/predictive structure can influence efficiency. Good predictive calibration and valid population-mean CIs are different goals [4, §2 p. 3].
- The same post-processed prediction must enter both prediction and rectifier terms. Using `g(S)` only in the unlabeled term generally destroys cancellation.
- Transforming the final mean estimate is a different task: `g(E[Y])` is generally not `E[g(Y)]`. No nonlinear target-transformation CI theorem was established by this reading; do not use prediction post-processing identities as one.

## 4. Cross-PPI: training on the label budget

**Source:** [3], Eq. (4) p. 5; Assumption 1/Theorem 1 pp. 7–8; Corollary 1 p. 8; variance construction §6 p. 11.

Partition labels into equal folds `I_1,...,I_K`. Train `f^(j)` without fold `I_j`. The exact mean estimator is

`mu_hat_cross = (KN)^{-1} sum_j sum_{i=1}^N f^(j)(tilde X_i) - n^{-1} sum_j sum_{i in I_j}(f^(j)(X_i)-Y_i)`.

It is unbiased under the stated train/held-out independence. Unlike plain PPI with separate training data, the summands are dependent through training, so an i.i.d. residual argument is insufficient.

Let `f_bar(x)=E[f^(1)(x)]`, and `sigma_bar^2=Var(f_bar(X))`, `sigma_bar_Delta^2=Var(f_bar(X)-Y)`. Assumption 1 requires

`sqrt(K Var(f^(1)(X)-f_bar(X) | f^(1))) → 0 in L1`.

For fixed K this is a stability/concentration condition, not consistency for the true conditional mean. Theorem 1 also assumes a limiting `n/N` and nonzero limiting variances. With consistent estimates,

`C_cross=mu_hat_cross ± z_(1-alpha/2) sqrt(sigma_hat_Delta^2/n+sigma_hat^2/N)`

has asymptotic coverage. This paper does not turn this into an unconditional finite-sample guarantee.

**Displayed practical variance estimator, §6:** bootstrap training sets of size `n-n/K`; train `B` models and average their predictions to obtain `f_bar_boot`. Set

`sigma_hat^2=Varhat_U(f_bar_boot(tilde X_i))`,

`sigma_hat_Delta^2=Varhat({f_boot^(b)(X_i)-Y_i: i not in training bootstrap b, b=1,...,B})`.

The residual computation specifically uses out-of-bootstrap observations, not in-sample fitted residuals. The text motivates bootstrap consistency via stability/conventional wisdom and validates coverage empirically; the cited mean CI corollary itself assumes consistent variance estimates. Do not overstate that discussion as a complete unconditional bootstrap theorem. Overlapping fits must not be counted as independent new labeled observations.

## 5. StratPPI: strata-specific corrections and sampling

**Source:** [4], §4 pp. 4–5, Eq. (8); Theorem 2/Eqs. (10)–(15) p. 5; Propositions 1–3 pp. 6–7; Example 1 Eq. (17) p. 7.

Predetermine a finite partition `A_k` with known masses `w_k`. Independently sample `n_k` labels and `N_k` unlabeled examples in each stratum. For means, specializing Eq. (8) gives

`mu_hat_strat=sum_k w_k [bar Y_Lk+lambda_k(bar S_Uk-bar S_Lk)]`.

For fixed weights and known stratum masses, its variance is

`sum_k w_k^2 [Var_k(Y-lambda_k S)/n_k + lambda_k^2 Var_k(S)/N_k]`.

The plug-in mean interval replaces each variance by its within-stratum empirical variance and is centered at the tuned estimator with normal multiplier `z_(1-alpha/2)`. The explicit mean optimal weight is

`lambda_k_star=Cov_k(Y,S)/[(1+n_k/N_k)Var_k(S)]`.

All moments here are conditional on the stratum. Theorem 2 assumes `n_k/n→rho_k>0`, `N_k/N→rho_tilde_k>0`, `n/N→r>=0`, consistent tuning, and regularity. Weights treated as known means this formula does not propagate estimation uncertainty in population stratum masses.

For fixed `lambda_k`, Proposition 3's scalar-mean allocation specializes to

`n_k proportional to w_k sqrt(Var_k(Y-lambda_k S))`,

`N_k proportional to w_k |lambda_k| sqrt(Var_k(S))`.

The conditional moments are generally unknown; zero oracle allocations need care because the theorem requires positive limiting allocation. Miscalibrated confidence-based allocation may lose efficiency, though a fixed positive allocation still satisfies the design's asymptotic validity conditions. Strata based on predicted scores, strata-specific tuning, and optimal allocation are already present here, not novel simply by being prediction-based.

**Apparent source inconsistency:** In the extracted [4] Algorithm 1 p. 6, line 11 displays a **plus** between true-label and weighted imputed-label gradients, whereas defining Eq. (11) p. 5 and rectified loss Eq. (8) require their **difference**. The mean variance above follows the defining loss/theorem, not that apparent algorithm sign typo. Example 1's covariance expression should also be read as centered linear regression (with intercept) when interpreting the regression analogy; the uncentered no-intercept objective in the prose does not in general yield a covariance/variance slope.

## 6. DML: orthogonality is conditional theory, not blanket black-box immunity

**Source:** [5], Definition 2.1/Eq. (2.3) p. 12; DML1/DML2 pp. 23–24; Assumptions 3.1–3.2 pp. 25–26; Theorems 3.1–3.2 p. 27; Corollary 3.1 p. 28.

DML starts with `E[psi(W;theta_0,eta_0)]=0` and requires Neyman orthogonality

`d/dt E[psi(W;theta_0,eta_0+t(eta-eta_0))] at t=0 = 0`.

Nuisances are trained off-fold. DML2 solves the pooled cross-fitted moment equation

`K^{-1} sum_k E_(n,k)[psi(W;theta_hat,eta_hat_k)]=0`.

For linear scores, with `J_hat=K^{-1}sum_k E_(n,k)[psi^a(W;eta_hat_k)]`, Theorem 3.2 gives

`Omega_hat=J_hat^{-1} [K^{-1}sum_k E_(n,k)[psi_i psi_i^T]] J_hat^{-T}`.

For scalar contrast `ell^T theta`, Corollary 3.1 returns

`ell^T theta_hat ± z_(1-alpha/2) sqrt(ell^T Omega_hat ell / M)`

where `M` denotes the total DML sample size here (the paper calls it `N`, unlike the separate unlabeled size in PPI). Coverage is **uniformly asymptotic** over the stated model classes, not finite-sample distribution-free. Required assumptions include moments, identification, nuisance accuracy, orthogonality, and fixed-fold cross-fitting. Smooth generic settings yield the sufficient crude rate `o(M^(-1/4))` for nuisance L2 error; the paper explicitly refines this in structured examples, and it is not a universal necessary rate. The introductory partially linear example pp. 4–6 shows the role of product errors and overfitting.

This is a useful boundary on claims about learned post-processors, not an automatic DML theorem for any proposed PPI estimator.

## 7. Source-grounded planning implications and novelty cautions

1. **Already present:** bias-corrected prediction mean [1]; arbitrary fixed black-box predictor [1]; optimal unrestricted scalar control weight, pooled plug-in tuning, and oracle asymptotic variance [2]; cross-fitting training within the label budget [3]; stratification on predicted outputs, stratum weights/tuning, and allocation optimization [4]; orthogonalization plus cross-fitting [5].
2. **Not established as new:** replacing `f` by fixed `g composed with f`, fitting a scalar, canceling an intercept, or deriving the oracle conditional-mean projection. Such algebra is not by itself a novelty claim.
3. **Unresolved by this restricted reading:** a general theorem for an adaptively learned nonlinear post-processor on the same labels; its finite-sample validity; efficiency of a particular finite-complexity class; or global novelty against literature outside the five papers. No claim is made about the unidentified prohibited paper.
4. If an experimental plan is later built, distinguish labeled-only, original PPI (`lambda=1`), and PPI++ (`lambda_hat`) baselines; preserve the training/calibration/inference budget; compare coverage, interval width, bias, and stability rather than width alone. These are planning implications, not an implementation request or a claim that new experiments were run.
5. Scope supports only a bounded comparison: no topic search, later-paper search, citation chasing, code verification, or dataset download was performed.

## 8. Evaluation protocols actually read (for planning only)

- **PPI++ [2], §7 pp. 12–14:** nominal `alpha=0.1`; independent labeled/unlabeled simulation samples; `N=10,000`; average coverage and CI width over **100 trials**. Mean simulation `Y~Normal(0,1)`, predictions `Y+sigma epsilon`, with `sigma=0.1,1,2`; compares `lambda=0`, `lambda=1`, plug-in tuning. These are noisy simulated predictions, not a model trained on the evaluation outcomes. The text reports implementation in `ppi-py`; no repository/package was accessed or verified.
- **Cross-PPI [3], §7 pp. 11–12:** coverage and width over **100 trials**; lower/upper endpoint standard deviations assess stability; synthetic `N=10,000`, labels `n=100,...,1000`, **K=10**, **B=30** bootstrap fits, `alpha=0.1`; data-split PPI spends half its labels on training. All methods use the same gradient-boosted-tree fitting strategy. Count those training labels when comparing efficiency. Text states experiment code is available; no repository was accessed.
- **StratPPI [4], §5 pp. 8–9:** synthetic `K=2`, equal masses, `N=10,000`, `alpha=0.1`, different stratum biases/noise; compares proportional and oracle allocation. **Reporting inconsistency:** Figure 1 caption says 5,000 trials while §5.1 prose says 1,000; do not silently choose one. Real data use **K=10**, nominal `alpha=0.05`, 1,000 trials in Figure 2, CI width/relative reduction/effective sample size. Predicted-score strata use discrete outputs or equal-mass score quantiles. The read text names Seahorse (2,727 examples for the selected summary-system/attribution task) and AttributedQA; no dataset links were followed. Confidence-based allocation is an efficiency heuristic, not a prerequisite that scores be calibrated for the stated fixed-design asymptotic coverage.

## Sources

[1] Prediction-Powered Inference: https://arxiv.org/pdf/2301.09633

[2] PPI++: Efficient Prediction-Powered Inference: https://arxiv.org/pdf/2311.01453

[3] Cross-Prediction-Powered Inference: https://arxiv.org/pdf/2309.16598

[4] Stratified Prediction-Powered Inference for Hybrid Language Model Evaluation: https://arxiv.org/pdf/2406.04291

[5] Double/Debiased Machine Learning for Treatment and Structural Parameters: https://arxiv.org/pdf/1608.00060
