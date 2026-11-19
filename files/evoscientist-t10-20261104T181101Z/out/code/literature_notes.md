# Allowlisted literature audit: mean controls and split calibration

## Status and source boundaries

This is a **partial original-source audit, not an experiment report**. Only the first three allowlisted original PDFs were downloaded; no references were followed and no external literature searches were performed. No attempt was made to identify the prohibited paper. Earlier full-PDF tool reads incidentally included bibliographies; the two affected sources were stopped as a precaution. See `/work/retrieval_log.md` for failures, corrections, and exposure details.

**Evidence labels:** **Verified [1]** means checked against physically page-restricted original PPI text in this continuation. **Independent derivation** means elementary analysis below, not a claim attributed to an unread theorem. **Unverified [2]/[3]** means mathematical content was not retained from earlier inspection and the stopped source was not reopened. Section labels alone are not evidence of theorem contents. Accordingly, this audit does **not** certify the precise PPI++ or stratified-PPI guarantees, nor settle whether either already covers a proposed postprocessing variant.

## 1. Verified original PPI findings

### Setup and assumptions

**Verified [1], §1.2, original p. 3:** labeled observations `(X_i,Y_i)` and unlabeled observations `X_tilde_j` are independent iid samples from the same population distribution. The prediction rule `f` is independent of both observed samples, e.g. trained on separate data. The population mean is the estimand, not the mean of the particular realized dataset. Distribution-shift and finite-population extensions are mentioned there but were not inspected here.

### Mean estimator and interval

**Verified [1], §1.3, original p. 3; §2.1, Proposition 1, p. 6; Algorithm 1, p. 7:** writing sample averages with subscripts `L` and `U`,

\[
\widehat\mu_{\rm PPI}=\overline{f(X)}_U-\overline{f(X)-Y}_L
=\bar Y_L+\overline{f(X)}_U-\overline{f(X)}_L.
\]

The two terms in the first expression are independent. Under the stated sampling and fixed-predictor assumptions the estimator is unbiased. Algorithm 1 uses

\[
\widehat\mu_{\rm PPI}\ \pm\ z_{1-\alpha/2}
\sqrt{\widehat{\operatorname{Var}}_L(f(X)-Y)/n+
\widehat{\operatorname{Var}}_U(f(X))/N}.
\]

Algorithm 1 uses empirical variances with divisors `n` and `N` (not the unbiased sample-variance divisors). **Its coverage guarantee is asymptotic:** Proposition 1 states a `liminf` coverage of at least `1-alpha` as `n,N` tend to infinity. §2.1 explicitly says its algorithms use the central limit theorem and regularity assumptions. Appendix C.3, which details those conditions, was not inspected; this audit therefore does not certify its exact full assumption list. Finite second moments and a suitable nondegenerate CLT regime are sufficient conditions for the usual fixed-control mean calculation, not a transcription of that appendix.

Good prediction does not guarantee improvement for every finite dataset. For a fixed control, improvement depends on residual variance **and** the nonzero unlabeled variance contribution. Prediction bias is removed by the rectifier; prediction accuracy alone is not an interval-width ordering.

### Finite-sample framework is already present

**Verified [1], §2, original p. 5, Theorem 1:** for nondegenerate convex estimation, define

\[
\Delta_\theta=E[g_\theta(X,Y)-g_\theta(X,f(X))],\qquad
q_\theta=E[g_\theta(X,f(X))].
\]

If, for each fixed `theta`, `R_delta(theta)` covers `Delta_theta` with probability at least `1-delta`, and `T_(alpha-delta)(theta)` covers `q_theta` with probability at least `1-(alpha-delta)`, then

\[
C_\alpha=\{\theta:0\in R_\delta(\theta)+T_{\alpha-\delta}(\theta)\}
\]

covers the target with probability at least `1-alpha`. The sum is a Minkowski sum. For means the gradient is `g_theta(y)=theta-y` and the rectifier is `E[f(X)-Y]` (§2.1, p. 6). The framework inherits the validity of its component confidence sets; it does not turn approximate Wald component sets into exact finite-sample sets.

The theorem is a finite-sample implication **conditional on valid component sets**. The statement following it says no assumptions on the ML model are needed; this must not be read as distribution-free, nontrivial, fixed-width concentration for arbitrary unbounded means. Actual component constructions require their own assumptions. §2.1 points to nonasymptotic algorithms in Appendix C.2, but that appendix was not inspected. **Finite-sample PPI itself is not a new contribution.**

### Novelty warning already in the original paper

**Verified [1], §1.4, original p. 4:** PPI explicitly identifies its mean estimator as the difference estimator and relates it to generalized regression/model-assisted estimation. It also distinguishes inference with a predictor fitted on separate data from same-data fitting, and states that both asymptotic and nonasymptotic variants exist. Those statements are from [1] itself; its cited works were not accessed, and this audit makes no separate claims about them.

## 2. Scalar versus nonlinear score controls — independent derivations

The following algebra supports comparison design but **is not a re-verification of [2]**. Let `S=f(X)` be an immutable scalar score. Let `D_train` contain any labels used to choose a transformation. Conditional on `D_train`, freeze a measurable transformation `g`. Use an independent labeled inference split of size `n` and an independent unlabeled sample of size `N`, from the same population. All variances below are conditional on `D_train`; assume the needed second moments exist.

\[
\widehat\mu_g=\bar Y_L+\bar g_U-\bar g_L,
\quad E[\widehat\mu_g\mid D_{\rm train}]=\mu,
\quad V_g=\frac{\operatorname{Var}(Y-g(S))}{n}
       +\frac{\operatorname{Var}(g(S))}{N}.
\]

Thus a learned score map can be valid without being an accurate conditional-mean estimator, **provided its evaluation samples are independent and its interval construction is valid**. Poor maps can still inflate variance. Simply calling a fitted map a fixed predictor does not establish independence.

### Scalar linear benchmark

For `g(s)=lambda*s+b`, the intercept cancels exactly. With `r=n/N`,

\[
nV_\lambda=\operatorname{Var}(Y)-2\lambda\operatorname{Cov}(Y,S)
 +(1+r)\lambda^2\operatorname{Var}(S).
\]

For `Var(S)>0`, the unrestricted oracle coefficient and variance are

\[
\lambda^*=\frac{\operatorname{Cov}(Y,S)}{(1+r)\operatorname{Var}(S)},
\qquad
V_{\lambda^*}=\frac{1}{n}\left[
\operatorname{Var}(Y)-\frac{\operatorname{Cov}(Y,S)^2}
{(1+r)\operatorname{Var}(S)}\right].
\]

If `Var(S)=0`, the contrast vanishes and gives no gain. The oracle class includes `lambda=0` (labeled-only) and `lambda=1` (original PPI mean estimator), so its **oracle variance** cannot exceed either. An estimated coefficient does not inherit a finite-sample no-worse-width/coverage guarantee from this algebra. Restrictions such as clipping the coefficient change the optimization problem; [2]'s precise constraints, tuning estimator, and theorem assumptions remain unverified here. Call this a **scalar power-tuned mean-control benchmark**, not a fully source-certified implementation of PPI++.

### What nonlinear maps can add

Write `m(s)=E[Y|S=s]`. Centering the control and completing the square gives

\[
nV_g=\operatorname{Var}(Y)-\frac{\operatorname{Var}(m(S))}{1+r}
 +(1+r)E\left[\left\{g(S)-E[g(S)]-
 \frac{m(S)-\mu}{1+r}\right\}^2\right].
\]

The unrestricted square-integrable oracle is therefore

\[
g^*(s)=\frac{m(s)}{1+r}+b,
\qquad V_{g^*}=\frac{E[\operatorname{Var}(Y\mid S)]}{n}
 +\frac{\operatorname{Var}(m(S))}{n+N}.
\]

This is an oracle identity **within this mean-control estimator family**, not a claim of global semiparametric efficiency or a new efficient-inference principle. It also shows why finite-`N` shrinkage matters; naively using `g=m` need not minimize this variance.

At equal inference sample sizes, the oracle advantage over the scalar class is

\[
V_{\lambda^*}-V_{g^*}=\frac{1}{n(1+r)}\left[
\operatorname{Var}(m(S))-\frac{\operatorname{Cov}(Y,S)^2}
{\operatorname{Var}(S)}\right]\ge0.
\]

There is no oracle nonlinear advantage when the conditional mean is affine in the score (up to null sets). Fitting error, hyperparameter selection, small strata, and labels consumed by training can erase an oracle advantage. Comparing these oracles at the same `n` does not show that a trained split method beats a scalar baseline using **all** original labels. Keep training, tuning, and inference label budgets explicit.

## 3. Postprocessing and stratification overlap

**Verified implication of [1]'s setup plus the derivation above:** for mean inference, applying PPI with a fixed transformed prediction `g(f(X))` has exactly the control form above. A nonlinear score transformation does not create a different debiasing principle. Label training is the additional statistical complication, not the algebraic rectification.

A fixed score partition `B_1,...,B_K` and values `a_k` define

\[
g(s)=\sum_{k=1}^K a_k 1\{s\in B_k\},\quad
\widehat\mu_g=\bar Y_L+\sum_k a_k(\widehat p_{U,k}-\widehat p_{L,k}).
\]

This is simultaneously a piecewise-constant score postprocessor and a vector of bin-indicator controls. With a fixed partition, the nonlinear oracle restricted to these controls uses shrunken conditional bin means. Therefore binning/poststratification is an essential overlap check and comparison, not automatically a distinct new method.

**Important non-equivalence:** the indicator-control identity does not establish equivalence to every stratified-PPI procedure. Stratified sampling/allocation, stratum-specific rectification, known versus estimated weights, and nuisance fitting can change the estimator and its variance. **Unverified [3]:** whether [3] already contains the proposed transformation, special case, or equivalent construction remains unresolved; no absence-of-overlap or novelty claim is justified from this partial audit.

A constraint distinction also needs clarification before any later experiments: transforming outputs leaves the base predictor's parameters unchanged, but it changes the predictions used for inference. If 'immutable predictor' forbids *all* output postprocessing rather than only retraining, this candidate is out of scope.

## 4. Split calibration and finite-sample coverage

### An explicit valid construction — independent derivation, not a new principle

Suppose, almost surely, `Y in [a,b]` and the frozen map `g(S) in [c,d]`. These must be genuine support bounds, not observed sample extrema. Set `R=Y-g(S)`, so a safe residual range length is

\[
L_R=(b-a)+(d-c),\qquad L_g=d-c.
\]

Choose error budgets `alpha_R+alpha_g=alpha` before looking at inference data. Conditional on the training data, separate two-sided Hoeffding bounds and a union bound yield

\[
\widehat\mu_g\ \pm\left[
L_R\sqrt{\frac{\log(2/\alpha_R)}{2n}}+
L_g\sqrt{\frac{\log(2/\alpha_g)}{2N}}
\right].
\]

Its coverage is at least `1-alpha` for every positive `n,N`, conditionally on training and hence unconditionally. The proof bounds `bar R-E R` and `bar g-E g` separately and uses `mu=E R+E g`. For equal budgets, both logarithms are `log(4/alpha)`. Intersecting this interval with `[a,b]` preserves coverage. A smaller prespecified almost-sure residual range can replace `L_R` if independently justified.

This illustrates how a label-trained transformation and finite-sample inference can coexist after honest splitting. It also fits the already verified rectifier-plus-prediction architecture of [1], Theorem 1. **Do not claim this concentration/splitting combination as a new validity or efficiency principle.** The displayed worst-case range bound is often conservative; narrower empirical residual variance does not itself narrow this particular radius.

### What 'split calibration' must specify

- Distinguish a population-mean interval from a prediction interval for a future individual. Exchangeable residual quantiles alone do not calibrate a population-mean confidence interval.
- Freeze the score map, bins, clipping, coefficient, model selection, and error-budget choices using a disjoint training/tuning subset, or supply a theorem covering their adaptivity. The simple conditional argument above requires both inference samples independent of that training procedure.
- A split by itself does **not** make a normal-quantile interval finite-sample valid. Studentization, bootstrap percentiles, and empirical coverage checks likewise do not establish universal finite-sample validity without additional conditions.
- A bound requiring known outcome/support limits cannot be advertised for arbitrary unbounded outcomes. Sample minima/maxima are not such limits.
- Cross-fitting could recover some split efficiency but creates shared-training dependence across fold estimates. Do not apply the independent-two-means variance formula to a pooled cross-fit estimator without a separate argument. Cross-PPI and DML were not read in this audit.
- If tuning chooses among intervals using inference labels, selects the narrowest split, or reuses an unlabeled sample to fit the map, the simple fixed-map conditional proof no longer suffices.

## 5. Recommended next comparisons (planning only; nothing run)

1. **Establish source gaps before implementation:** verify [2]'s precise scalar mean estimator, power constraints, plug-in tuning, and asymptotic assumptions; verify [3]'s estimator/weighting/allocation and score-strata special cases. Both are currently stopped; a renewed source-reading approach would need explicit authorization consistent with the source-boundary restriction. Do not silently reopen them. The other allowed sources remain unread.
2. **Use a nested comparison:** labeled-only, original PPI (`lambda=1`), properly verified scalar PPI++, affine score map (an algebraic check, not an independent method), fixed-bin indicator controls, and label-trained nonlinear score maps. Include constant-score and affine-conditional-mean null cases where nonlinear gains should disappear, and a nonlinear-conditional-mean case to expose approximation rather than debiasing gains. Oracle controls can diagnose headroom but must not be reported as feasible methods.
3. **Separate statistical and budget effects:** compare scalar versus nonlinear maps on the same held-out inference split, then compare full procedures with the same total labels including training/tuning costs. Use the same realized inputs across methods within each repetition. Do not add labels or retrain the immutable base predictor.
4. **Separate validity regimes:** label Wald intervals asymptotic and bounded-outcome concentration intervals finite-sample under stated bounds. Compare widths only alongside their actual coverage and assumptions; an under-covering interval is not an efficiency win. Report unsuccessful or wider intervals too.
5. **Later evaluation protocol:** repetitions must regenerate the sampling process relevant to the claimed population target while sharing inputs across methods within a repetition. Report nominal level, empirical repeated-sampling coverage with Monte Carlo uncertainty, mean/median width and paired width differences with uncertainty, training/inference sizes, `N/n`, split randomness, clipping/bin/model choices, empty-bin behavior, and timing. Repeatedly repartitioning one fixed dataset measures split sensitivity, not automatically population repeated-sampling coverage. No dataset, numerical result, code availability claim, or empirical improvement was verified in this audit.

## 6. Novelty assessment and limits

**Defensible framing:** an empirical and methodological audit of when fixed-score nonlinear controls improve on a scalar power-tuned baseline after accounting for label costs and interval calibration. Potentially useful deliverables include transparent negative results, a careful comparison protocol, and an explicit width-versus-coverage tradeoff under bounded-outcome split inference.

**Not justified:** a new efficient-inference principle; first use of prediction-based debiasing or finite-sample PPI; first use of nonlinear score transformations, bin controls, or stratification; guaranteed finite-sample dominance of a learned method; or a completed PPI++/stratified-PPI novelty clearance. No exhaustive novelty conclusion is possible under the current restricted and incomplete evidence.

## 7. Exact inspected material and provenance

### [1] Prediction-Powered Inference — verified content retained

Original PDF: https://arxiv.org/pdf/2301.09633 . Downloaded file identifies itself as arXiv:2301.09633v4, 9 Nov 2023. Safely read only original pages **1–7** via physically restricted derivatives; no bibliography pages included.

- p. 1: title, authors, abstract, opening §1.
- p. 2: §1.1 general principle and figure.
- p. 3: §1.2 assumptions; §1.3 mean estimator and illustrative Wald interval.
- p. 4: continuation §1.3; §1.4 related work as written in this original (no cited sources followed); opening §2.
- p. 5: §2 Eq. (1) nondegeneracy, Eq. (2) rectifier, component sets, Theorem 1 and accompanying discussion.
- p. 6: §2.1 preamble; mean target Eq. (3), squared-loss gradient/rectifier, Proposition 1; quantile/logistic portions visible but not used for mean claims.
- p. 7: Algorithm 1, all four steps; other regression/quantile material visible but not used for mean claims.
- Not inspected: Appendix C.2 finite-sample algorithms, C.3 precise regularity conditions, E mean confidence constructions, distribution-shift/finite-population extensions, datasets/code links.

Local page-restriction utility: `/work/restrict_pdf_pages.py` (standard library; intentionally limited parser). Derivatives: `/work/sources/2301.09633_pages1-3.pdf`, `2301.09633_page4.pdf`, `2301.09633_page5.pdf`, `2301.09633_page6.pdf`, `2301.09633_page7.pdf`. Physical page selection was necessary because native PDF `offset/limit` had returned entire PDFs. No new software was downloaded or installed.

### [2] PPI++ — prior inspection recorded, mathematical verification incomplete

Original allowlisted URL: https://arxiv.org/pdf/2311.01453 . Local `/work/sources/2311.01453.pdf`.

Earlier log records §§2–3 (Algorithm 1, Corollaries 1–2), §4 (Theorem 1, Proposition 1, Algorithm 2), §§6.1–6.2 (Proposition 2, Eq. 8, Example 6.1), §7.1, Appendix A.1 Definition A.1, Appendices B/C. **Actual theorem/formula content was not retained in accessible notes; these are inspection-history identifiers only, not verification for claims above.** Whole-PDF tool output incidentally included bibliography pp. 18–20. Source stopped; not reopened.

### [3] Stratified PPI — prior inspection recorded, mathematical verification incomplete

Original allowlisted URL: https://arxiv.org/pdf/2406.04291 . Local `/work/sources/2406.04291.pdf`.

Earlier log records §§3–3.2 (Eqs. 1–7, Theorem 1, Corollary 1), §§4–4.3 (Eqs. 8–21, Algorithm 1, Theorem 2, Corollary 2, Propositions 1–3, Examples 1–2), §§5.1–5.2/Figures 1–2 captions, §6 Limitations, Appendix A Definition A.1/A.1–A.5 proof checks, Appendix B Eqs. 60–63, Appendix C/Figure 3. **Mathematical content was not retained; no detailed theorem attribution is made.** Whole-PDF tool output incidentally included bibliography pp. 11–14. Source stopped; not reopened.

### Unread permitted sources

2309.16598, 2403.03208v2, and 1608.00060 were not downloaded/read. No claims about their results, protocols, implementations, or overlap are made.
