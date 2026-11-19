# Baseline context: fixed-score inference for a population mean

This is supplied context for study planning and feasibility. It records checked sources and elementary consequences, not measured results, an implementation audit, or a claim that the proposed method is new. All sources below were accessed directly at the listed permitted URLs on 2026-11-02. No broad literature or citation-chain search was performed.

## 1. Precise observation model and question

Let S=f(X) be the frozen prediction. Observe n iid pairs (Y_i,S_i) and N independent iid scores S'_j from the same score marginal. The target is μ=E[Y], not E[S]. Condition on the external model, which is independent of these inference samples. Compare methods on identical input records per replicate. Keep the DGP/model fixed while independently repeating the sampling experiment.

For empirical real-data experiments, iid resampling with replacement from a file of paired labels/predictions yields a known empirical-distribution target: the full file mean. Hide all evaluation-only labels from fitting/tuning. This is an empirical-population experiment and does not establish coverage for a new scientific population without representativeness assumptions. Sampling without replacement from a finite file and holding an unlabeled census fixed is a different design; use the corresponding variance theory rather than silently reuse the independent-sample formula.

The narrow research question can be: how much does a prespecified nonlinear, low-dimensional score control improve width over an optimally tuned scalar score control, and when does fitting cost or finite-sample non-normality remove that gain? This respects the immutable base predictor if its outputs and parameters remain unchanged and learned coefficients are explicitly inference nuisance quantities. Planning should record that interpretation; it must not be portrayed as a newly trained feature predictor.

## 2. Existing mean baselines and what their validity means

**Label-only.** The mean is Ybar. A normal interval uses estimated Var(Y)/n. It is a CLT interval under finite moments and nondegeneracy, not an exact general finite-sample procedure. Bounded-data concentration intervals supply a separate valid finite-sample comparator; exact binomial intervals are another available option when Y is genuinely Bernoulli.

**Original PPI.** Angelopoulos et al., arXiv:2301.09633v1, §1.2–1.3 and §2.1, define an external fixed f and iid samples from one population. For means, μhat=mean_U(S)+mean_L(Y−S), with variance Var(Y−S)/n+Var(S)/N. The main practical algorithms are CLT-based (§2.1 explicitly says so). Theorem 1 is also a general finite-sample construction: if valid confidence sets for the rectifier and prediction mean are supplied, their Minkowski sum/union-bound inversion has coverage at least 1−α. Thus “PPI is only asymptotic” is too broad; specify the particular normal-interval implementation. The paper also treats finite populations and certain distribution shifts, but that is not license to apply the iid formula unchanged.

**Power-tuned PPI++.** Angelopoulos, Duchi and Zrnic, arXiv:2311.01453v1, §2.2, Theorem 1/Corollary 4, and Example 6.1, give

    μhat_λ = Ybar_L + λ(Sbar_U−Sbar_L),
    V(λ) = Var(Y−λS)/n + λ² Var(S)/N,
    λ* = Cov(Y,S)/[(1+n/N) Var(S)].

The plug-in coefficient uses labeled covariance and a pooled score-variance estimate. Consistency of the tuned coefficient, appropriate finite moments and a nonzero limiting variance yield asymptotic normal inference. The improvement/no-worse-than-label-only claim is a first-order asymptotic claim, not a guarantee for each dataset, at all small n, or after arbitrary data-driven model selection. Constants in f are corrected by the labeled residual mean; prediction bias alone does not invalidate the rectifier.

For mean estimation the paper explicitly allows **λ in all of R**, with no need to clip for convexity. For other losses clipping/one-step corrections address convexity, which does not justify imposing [0,1] as a theoretical mean-optimality restriction.

**Version-specific code distinction.** The allowed reference package v0.2.3 source was retrieved directly from `https://raw.githubusercontent.com/aangelopoulos/ppi_py/v0.2.3/ppi_py/ppi.py`. In `ppi_mean_ci` and `ppi_mean_pointestimate`, automatic tuning calls `_calc_lam_glm(..., clip=True)`; that helper applies `np.clip(lam,0,1)`. Its normal standard errors use NumPy std with its default ddof=0. Therefore report the package default as **clipped PPI++ v0.2.3**, and include unrestricted scalar tuning to match the mean theory. If a hand implementation differs in ddof or degenerate-score handling, document the difference and verify parity; do not attribute all deviations to new methodology.

A nonlinear method may beat clipped PPI++ simply because a score is negatively associated with Y or needs a slope greater than one. That is already addressed by unrestricted scalar PPI++, and is not evidence for nonlinear information. An unrestricted scalar diagnostic is indispensable for that claim.

## 3. What nonlinear controls can and cannot promise

The following are elementary control-variate consequences of the variance objective, provided to delimit claims. They are not assertions of novel theory. Let h(S) be a square-integrable, fixed correction, and define μhat_h=mean_L(Y−h(S))+mean_U h(S). Its variance is

    V(h) = Var(Y−h(S))/n + Var(h(S))/N.

Set r=n/N and m(S)=E[Y|S]. Minimizing over score-measurable h, up to an arbitrary additive constant, gives h*(S)=m(S)/(1+r). The resulting scaled variance is

    n V* = E Var(Y|S) + [r/(1+r)] Var(m(S)).

For a finite vector of score features φ(S), with nonsingular covariance Q and c=Cov(φ(S),Y), the oracle coefficient is β*=Q⁻¹c/(1+r). Singular bases require a projection/pseudoinverse interpretation or a reduced basis, not a silent inversion.

The oracle variance improvement of the unrestricted score-function class over unrestricted scalar tuning is

    n(V_scalar*−V_score*)
      = [ Var(m(S)) − Cov(Y,S)²/Var(S) ]/(1+r),

when Var(S)>0. This is nonnegative by projection. It vanishes when m is affine in S; if Y has no conditional-mean signal, no such first-order gain is available. For a score taking only two values, every function on its support is affine: nonlinear score bases add no oracle mean information. A finite cubic basis only captures the component of m in its span; it need not attain the all-functions oracle.

These statements concern a particular oracle class and leading variance, not a universal impossibility theorem for every valid confidence interval, every nonregular procedure, use of extra covariates X, or finite-sample width. Learning a flexible correction from n labels adds finite-sample costs. Cross-fitting can reduce fitting bias but does not guarantee short intervals or exact finite-sample coverage. Any asymptotic theorem for a learned correction must state a convergence/stability condition and prove the remainder is negligible for the actual construction, including reuse of unlabeled records across folds.

This is established control-variate/semi-supervised logic. PPI++ §2.3 explicitly relates its mean estimator to AIPW and §6 discusses efficiency. The supplied Cross-PPI paper §2.1 also explicitly describes earlier projection corrections involving low-degree polynomials. Consequently the paper should present a transparent investigation/application under fixed inputs, not claim first invention of nonlinear prediction controls, cross-fitting, or an unconditional optimal method.

## 4. Other permitted methods: fair scope distinctions

**Cross-Prediction-Powered Inference.** Zrnic and Candès, arXiv:2309.16598v1, §2–4 and Assumptions 1–2/Theorems 1–2: trains fold-specific prediction functions from available labels and debiases held-out predictions, with asymptotic validity under prediction stability. This is relevant precedent for learning nuisance corrections without wasting all split-off labels. Its headline comparison includes training/fine-tuning the underlying predictor, so that version is outside the frozen-predictor constraint. A score-only cross-fitted nuisance is related but should not be called an exact reproduction of its full training procedure. Cross-fitting alone is not its theorem's only hypothesis.

**Active Statistical Inference.** Zrnic and Candès, arXiv:2403.03208v2, §2: chooses which new labels to acquire, with an expected labeling budget, including batch/fixed-model and sequential/updating variants. It establishes benefits from changing the acquisition policy. Those benefits do not answer a question where label identities are already fixed. It is relevant related work, not a permissible comparator that gets to purchase different labels.

**Stratified PPI.** Fisch et al., arXiv:2406.04291v1, §4, Theorem 2 and Proposition 1: uses a prespecified partition, treats stratum population masses w_k as known, and draws fixed n_k,N_k within strata; estimates stratum-specific tuning and can optimize allocations. Its guarantee is asymptotic. Even proportional allocation can improve precision under that design, but retrospective iid data have random stratum counts and estimated masses. Allocation-driven benefits change the fixed input samples and cannot be claimed here. A fixed-input poststratified/bin-indicator control comparator is possible, but its mass estimation and variance must match our sampling scheme. Treating empirical unlabeled masses as known constants discards sampling uncertainty. Planning must either include a suitable fixed-input comparator or explain this design mismatch and narrow any superiority claim. This is the closest explicitly permitted alternative exploiting conditional heterogeneity; do not silently omit its relationship.

**Double machine learning.** Chernozhukov et al., arXiv:1608.00060v1, Introduction: orthogonal estimating equations and K-fold cross-fitting address regularization/overfitting bias for low-dimensional parameters with learned nuisances. The directly read v1 is titled “Double Machine Learning for Treatment and Causal Parameters” and has six authors (Chernozhukov, Chetverikov, Demirer, Duflo, Hansen, Newey); do not mix its metadata with a later expanded version. This source supports the general principle, not a ready-made exact theorem for our estimator or a requirement to conduct causal inference.

## 5. Finite-sample bounded-data branch

Maurer and Pontil, “Empirical Bernstein Bounds and Sample Variance Penalization,” arXiv:0907.3740v1 (directly retrieved; old unrelated foundational source), Theorem 4, assumes iid Z in [0,1] and n≥2. It gives the one-sided deviation

    E[Z]−Zbar ≤ sqrt(2 s² log(2/δ)/n) + 7 log(2/δ)/(3(n−1)),

where s² is the unbiased sample variance. Apply the same theorem to 1−Z and a union bound to obtain a two-sided bound; account for both tails explicitly. For a variable with known range length B the additive term scales by B and the variance term uses its variance in original units. Sample extrema are not a known support bound.

A correction trained on an independent split can be conditioned on, bounded/clipped to a declared support, and combined with independent residual-mean and prediction-mean bounds using a prespecified error allocation. The iid, range, conditional-independence and tail-allocation arguments belong in the analysis proof. Using training residuals as if the fitted function were fixed would invalidate this argument. Preserve label-only and scalar finite-sample comparators, and report the loss of effective labeled sample size from training. Intersecting an interval with a genuinely known parameter range preserves coverage; arbitrary width-based selection among separately valid intervals does not, unless covered by a simultaneous guarantee or a valid selection construction.

An empirical-Bernstein guarantee may be conservative and much wider than normal intervals. Compare width primarily within a guarantee class and label both. A successful finite-sample construction need not improve every scenario; absence of a measured gain is an acceptable answer. Monte Carlo coverage fluctuates: report uncertainty and predefine how practical evidence of undercoverage is judged, rather than demand every coverage point estimate exceed exactly 0.95 or declare exact validity from a nonsignificant test.

## 6. Data context and reporting conventions

The supplied data guide is acquisition metadata, not independently inspected arrays. Galaxy Zoo 2 (Willett et al., arXiv:1308.3496v1, abstract) is a 304,122-galaxy citizen-science morphological catalog with classification-bias analysis; the PPI galaxies file is a smaller derived subset. Do not imply its crowdsourced reference labels are error-free physical truth or that the empirical-file mean is the universe's spiral fraction. Folktables (Ding et al., arXiv:2108.04884v1, abstract/introduction) explicitly studies geographic/temporal context and external-validity limitations of Census-based benchmarks. The UCI Wine Quality dataset metadata (direct API dataset 186) confirms physicochemical features and sensory quality scores; it supplies no frozen model. These dataset sources establish provenance, not our method's coverage.

PPI++ §7.1 reports width and coverage over 100 trials at nominal 90%; StratPPI §5/Figures 1–2 uses 1000 trials, mean widths and 16/84-percentile bands. These are prior conventions, not required replication counts. Our objective asks uncertainty reports, so Monte Carlo intervals for coverage and paired standard errors/intervals for width effects are appropriate. Distinguish variation across interval widths from uncertainty in their mean: percentile spread bands and Monte Carlo confidence intervals answer different questions. State seeds, replicate counts, target, nominal coverage, sampling scheme, ratios' direction, and whether intervals are clipped to known support. Never reuse published numbers as our measured results.

## 7. Source evidence map

Exact arXiv PDF URLs and SHA-256 values are in `sources/access.json`. Retained text paths below give checkable evidence; the full PDFs can be fetched with `sources/fetch_context.py`.

| Source | Checked loci | Use |
|---|---|---|
| PPI 2301.09633v1 | §1.2–1.3, §2.1, Theorem 1; sources/ppi.txt | Sampling assumptions, mean correction, finite/asymptotic distinction |
| PPI++ 2311.01453v1 | §2.2–2.3, Theorem 1, §6/Example 6.1, §7.1; sources/ppiplus.txt | Essential scalar baseline; unrestricted coefficient; existing efficiency positioning |
| Cross-PPI 2309.16598v1 | §2.1, §3–4, Assumptions 1–2/Theorems 1–2; sources/crossppi.txt | Cross-fitting/stability and distinction from fixed base predictor |
| Active 2403.03208v2 | §2; sources/active.txt | Acquisition-policy difference |
| StratPPI 2406.04291v1 | §3–4, Theorem 2, Proposition 1, §5 figure captions; sources/stratified.txt | Conditional heterogeneity, design/mass assumptions and reporting |
| DML 1608.00060v1 | Introduction; sources/dml.txt | Cross-fitting/orthogonalization precedent |
| Maurer–Pontil 0907.3740v1 | Theorem 4; sources/empirical-bernstein.txt | Exact bounded-data concentration assumption/constants |
| Folktables 2108.04884v1 | Abstract/introduction; sources/folktables.txt | Optional Census-data context and external validity |
| Galaxy Zoo 2 1308.3496v1 | Abstract/introduction; sources/galaxyzoo.txt | Derived galaxy-data provenance |
| UCI dataset 186 | sources/wine-uci.json | Optional wine data's scope/variables |
| ppi_py v0.2.3 | ppi_mean_ci, ppi_mean_pointestimate, _calc_lam_glm; sources/ppi-v0.2.3.py | Implementation-specific clipping and variance convention |

The review is intentionally bounded by the independence restriction. It establishes neither exhaustive priority nor absence of other relevant methods. The study's theoretical and empirical contributions must be stated without a global novelty claim.
