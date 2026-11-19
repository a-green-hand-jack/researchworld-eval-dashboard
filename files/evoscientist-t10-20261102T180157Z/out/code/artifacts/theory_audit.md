# Independent adversarial audit of `/work/theory.md`

final-status: REFUTED

The **literal bundle** has counterexamples, but its central oracle calculation and finite-dictionary confidence construction survive. The refutation concerns omitted fold-assignment conditions, an overstated ridge convergence rate, and unspecified outcome distributions in the synthetic variance claims. It does not refute the repaired asymptotic estimator or the finite-sample dictionary theorem.

## Scope and evidence

Only the clean statement and mathematical reasoning were used. No web search, papers, experiment code/results, or other research-task documents were consulted. A required memory preflight exposed a paper-derived observation; its substantive contents were excluded. The skill supplied procedural audit guidance only. All calculations below are analytic, not numerical evidence.

For an independently trained but random frozen predictor, interpret all distributional assertions **conditional on that predictor**. The displayed variances are then conditional variances; averaging conditional variances is needed for an unconditional numerical variance. Sample budgets and their ratio are deterministic.

## 1. Findings ordered by severity

| Severity | Location | Status | Finding and precise repair |
|---|---|---|---|
| **High** | B: balanced crossfit folds | **INCORRECT if balance is the only fold restriction** | Score-dependent balanced folds can make the estimator inconsistent, even with bounded features and nonsingular within-fold limiting covariance. Require a deterministic partition of indices, or a random partition independent of observations. See the exact counterexample in §2.1. Under the conventional independent-fold meaning of “crossfit,” this is a necessary clarification rather than a failure of the intended method. |
| **Medium** | B: coefficient and product rates | **INCORRECT for arbitrary `epsilon_n -> 0`** | The generic coefficient rate is `O_p(n^(-1/2)+epsilon_n)`, not necessarily root-n. The remainder is correspondingly `O_p(n^(-1)+epsilon_n n^(-1/2))`. Vanishing epsilon still suffices for first-order equivalence. The proposed `epsilon_n=1e-4/n` repairs the claimed rates. See §2.2. |
| **Medium** | Synthetic `VarY` values | **INCORRECT under the stated conditional-mean information alone** | Specifying `m(S)` does not specify `Var(Y)`. Taking `Y=m(S)` refutes all three displayed nonconstant-case `VarY` values. Add `Y given S ~ Bernoulli(m(S))`; then every displayed synthetic formula is correct. See §2.3 and §7. |
| **Low / domain** | B: regression definition | **UNDER-SPECIFIED** | Give the ridge objective/normal equations, take fixed `K>=2`, and define a fallback on singular finite-sample designs. A penalty proportional to the empirical covariance does not remove its nullspace. These issues do not prevent the repaired pointwise asymptotic proof. |
| **Low / domain** | A, C | **NEEDS EXPLICIT DOMAINS** | The scalar statement requires `0<Var(S)<infinity`. C requires `0<alpha<1` and `n,N>=2` for its displayed sample variances/radii. A known constant variable has radius zero; an empirically constant sample does not establish a zero population range. |

**Positive findings:** A's identity, optimum, equality conditions, and no-gain conditions are **PROVED**. B's repaired first-order equivalence, variance consistency, and normal CI are **PROVED ASYMPTOTIC STATEMENTS**, not finite-sample coverage claims. C is a **PROVED FINITE-SAMPLE THEOREM** with the stated ranges and multiplicity allocation, after making its sample-size domains explicit; §6 proves its concentration ingredient without accessing the cited paper.

## 2. Counterexamples first

### 2.1 Balance without observation-independent folds can destroy consistency

Let `S ~ Uniform[0,1]`, `Y=S^2`, `h(S)=S`, and take even n. Use two exactly balanced folds obtained by sorting the labeled scores: the lower half and the upper half. Use the intercept in regression and let the ridge penalty vanish. The empirical median converges to `1/2`; the law of large numbers and boundedness give convergence of each half's empirical moments to those of its corresponding half-uniform distribution. This satisfies boundedness and finite second moments. The limiting training-feature variance in either half is `1/48>0`.

For a uniform variable on `[u,v]`, the regression slope of `S^2` on `S` with an intercept is `u+v`: writing `S=c+Z`, with `c=(u+v)/2` and symmetric centered `Z`, gives

`Cov(S,S^2)=2c Var(S)`.

Consequently, the coefficient trained on the upper half converges to `3/2`, and that trained on the lower half converges to `1/2`, whereas the full-population slope is `1`. The held-out score means converge to `1/4` and `3/4`; the unlabeled score mean converges to `1/2`. The correction therefore converges to

`[ (3/2)(1/2-1/4) + (1/2)(1/2-3/4) ] / [2(1+r)] = 1/[8(1+r)].`

Thus the estimator converges to

`1/3 + 1/[8(1+r)]`,

not to `mu=1/3`. At `r=1`, its limit is `19/48`, with bias `1/16`.

**Repair:** folds must be assigned independently of the observations, with each fold and its training complement having order-n size. Balance concerns sizes; it does not supply independence or zero-mean held-out moment differences.

### 2.2 Vanishing ridge does not imply root-n coefficient error

Use `S ~ Uniform[0,1]`, `Y=S`, `h(S)=S`, and ordinary independent folds. Interpret “penalty epsilon times empirical covariance” literally as adding `epsilon_n b^2 hatSigma` to centered empirical squared loss. Almost surely the training covariance is positive, and the fitted slope is exactly

`b_-k = 1/(1+epsilon_n)`.

The projection coefficient is `b=1`. With `epsilon_n=n^(-1/4)`, the coefficient error is asymptotic to `-n^(-1/4)`, not `O_p(n^(-1/2))`. Since all folds have the same coefficient, the estimator-minus-oracle remainder is

`-epsilon_n / [(1+epsilon_n)(1+r_n)] * (mean_U S - mean_L S)`.

For `n=N`, the factor `sqrt(n)(mean_U S-mean_L S)` has a nondegenerate normal limit. The remainder is of order `n^(-3/4)`, and is not `O_p(n^(-1))`.

It is nevertheless `o_p(n^(-1/2))`. Hence this counterexample refutes the claimed intermediate rates, **not** first-order equivalence under consistent coefficients. Conventional ridge with a bounded nonzero penalty matrix has the same potential epsilon-order bias.

### 2.3 A conditional mean is not an outcome law

Set `Y=m(S)` deterministically in each synthetic model. This satisfies `E[Y|S]=m(S)` and even `0<=Y<=1`, but gives:

- Linear: `Var(Y)=0.64/12=4/75`, not `0.25`.
- Quadratic: `Var(Y)=0.08192`, not `0.2244`.
- Step: `Var(Y)=0.2401`, not `0.25`.

The missing term is `E[Var(Y|S)]`. The displayed values follow if outcomes are Bernoulli conditional on `S`, because then the marginal outcome is Bernoulli with success probability `mu`.

## 3. Claim A: exact oracle statement — PROVED

Write `r=n/N`, let `g(S)` be deterministic and square-integrable, and let `m(S)=E[Y|S]`. Conditional Jensen ensures `m` is square-integrable. Independence of the two samples gives

`E[muhat_g]=mu`,

and

`n V(g) = Var(Y-g(S)) + r Var(g(S))`

`= Var(Y) - 2 Cov(Y,g(S)) + (1+r) Var(g(S)).`

The conditional-expectation identity `Cov(Y,g(S))=Cov(m(S),g(S))` then gives the centered-square identity

`n V(g) = Var(Y) - Var(m)/(1+r) + (1+r) Var(g-m/(1+r)).`

Every term is finite under the hypotheses. It follows that the minimum is attained precisely when

`g(S)=m(S)/(1+r)+c` almost surely,

for some constant `c`. Constants cancel from the estimator exactly.

For the scalar subclass, assume **finite positive** `Var(S)`. Completing its one-dimensional quadratic gives

`lambda* = Cov(Y,S)/[(1+r) Var(S)]`,

`n V(lambda* S) = Var(Y) - Cov(Y,S)^2/[(1+r)Var(S)]`,

and

`V(lambda* S)-V(g*) = [Var(m)-Cov(Y,S)^2/Var(S)]/[n(1+r)].`

Indeed, putting `beta=Cov(m,S)/Var(S)`, the numerator equals

`E[((m-E[m])-beta(S-E[S]))^2]`.

It vanishes if and only if `m(S)` is affine in `S` almost surely, including a constant affine function. This is an almost-sure condition under the score distribution, not an identity required off its support. For constant `S`, every score-measurable control and `m(S)` is constant, so both subclasses give `Var(Y)/n`.

The optimum's gain relative to no predictions is exactly

`Var(m)/[n(1+r)]`.

It is zero if and only if `m(S)` is almost surely constant. This means conditional-mean uninformative, not necessarily independent of `Y` for general nonbinary outcomes. The scalar subclass alone has zero gain if and only if `Cov(Y,S)=0`; these two conditions differ, as the quadratic example demonstrates.

An invertible affine score transformation preserves the scalar control class modulo constants, and therefore preserves its optimally tuned variance. All real scalar coefficients are admissible; there is no restriction to `[0,1]` in this mean-estimation calculation.

As a budget sanity check,

`V(g*) >= r Var(Y)/[n(1+r)]`,

because `Var(m)<=Var(Y)`. With positive finite `r`, oracle variance cannot vanish when `Var(Y)>0`.

**Scope:** these are exact variance comparisons among fixed score-measurable additive controls at the same budgets. They are neither finite-sample CI coverage/dominance statements nor lower bounds over arbitrary estimators or richer covariates. They do not automatically give the finite-sample variance of a control fitted on the same observations.

## 4. Claim B: repaired pointwise asymptotic theorem

### 4.1 Precise sufficient assumptions

Use a fixed data-generating distribution with `Y in L2`, a deterministic bounded `p`-vector `h`, fixed `p`, and

`Sigma=Cov(h(S))` positive definite; `c=Cov(h(S),Y)`; `beta=Sigma^(-1)c`.

The intercept is separate: do not include a duplicate constant coordinate in `h`. Take deterministic budgets with `n,N -> infinity`, `r_n=n/N -> r in (0,infinity)`. Assign a fixed number `K>=2` of folds independently of all observations, with deterministic sizes satisfying `n_k/n -> q_k in (0,1)`; the advertised balanced case is `q_k=1/K`. A deterministic partition of indices also qualifies. Let `w_k=n_k/n` **exactly**.

Define the regression fit on singular finite-sample designs by a specified fallback or generalized inverse. For example, on nonsingular training covariance matrices take

`b_-k = (hatSigma_-k + epsilon_n M_-k)^(-1) hatc_-k`,

where `M_-k` is positive semidefinite, formed from that training fold-complement only, and `O_p(1)`, and the deterministic penalty obeys `epsilon_n>=0`, `epsilon_n -> 0`. A covariance-proportional penalty is included on nonsingular designs. Since training covariances converge to the positive definite `Sigma`, singularity has probability tending to zero. Any everywhere-defined finite training-only fallback on that event suffices for the assertions in probability here.

Set

`g_-k(s)=b_-k^T h(s)/(1+r_n)`,

and form exactly the estimator in the clean statement. With these definitions it has the first-order behavior proved below.

### 4.2 Regression rates and the actual requirement

Boundedness of `h` and `Y in L2` make empirical cross-moments root-n consistent; covariance estimates are also root-n consistent. Matrix inversion is locally continuous and Lipschitz around positive definite `Sigma`. Subtracting the population normal equations gives

`b_-k-beta = O_p(n^(-1/2)+epsilon_n)`.

For example, when the inverse exists,

`b_-k-beta = (hatSigma_-k+epsilon_n M_-k)^(-1)`

`                 * [hatc_-k-c - (hatSigma_-k-Sigma)beta - epsilon_n M_-k beta]`.

Thus:

- `epsilon_n -> 0` implies coefficient consistency, which is enough for the asymptotic theorem.
- `epsilon_n=O(n^(-1/2))` suffices for the asserted root-n coefficient rate and `O_p(n^(-1))` remainder.
- The proposed `epsilon_n=1e-4/n` satisfies that stronger condition.
- A fixed positive epsilon need not converge to the projection coefficient. If its population penalized limit exists, the same first-order argument can target that **shrunk** control, but exact projection/oracle efficiency is then not justified. “Practically negligible” is not a universal mathematical bound.

### 4.3 Exact remainder: balance, dependence, and reused unlabeled scores

Define the deterministic projection control

`g_n^0(s)=beta^T h(s)/(1+r_n)`.

The exact fold weights satisfy

`sum_k w_k mean_Lk h = mean_L h`.

Consequently the corresponding fixed-control estimator is exactly

`mutilde_n = mean_L Y + beta^T (mean_U h - mean_L h)/(1+r_n)`.

Subtracting gives the exact identity

`muhat_CF-mutilde_n = sum_k w_k (b_-k-beta)^T D_k/(1+r_n)`,

where `D_k=mean_U h-mean_Lk h`.

For every independently assigned fold, `E[D_k]=0` and `E[||D_k||^2]=O(1/N+1/n_k)=O(1/n)`. Conditional on the observation-independent index partition, the coefficient is independent of its own held-out fold and of the unlabeled sample. However, the different coefficients overlap in their training data, and all `D_k` reuse the same unlabeled mean. No joint independence is asserted or needed: fixed `K`, the triangle inequality, `D_k=O_p(n^(-1/2))`, and `b_-k-beta=o_p(1)` already imply

`muhat_CF-mutilde_n = o_p(n^(-1/2))`.

With the ridge rate above, the sharper valid bound is

`O_p(n^(-1)+epsilon_n n^(-1/2))`.

This proof explains exactly why mere consistency is sufficient, why observation-dependent sorted folds fail, and why reuse of the unlabeled sample causes no first-order fitting penalty in this fixed-dimensional regime. One should not condition jointly on all fitted coefficients and claim that all held-out observations remain iid; that stronger conditional assertion would generally be false.

Exact balance is not otherwise essential: fold proportions bounded away from zero and one suffice. The exact `n_k/n` weights are what recover the original full labeled mean for a fixed control. Using equal `1/K` weights for folds differing by at most one observation is asymptotically harmless here but is not the same finite-sample identity.

### 4.4 CLT and limiting variance

Let `g^0(s)=beta^T h(s)/(1+r)` and `v=c^T Sigma^(-1)c`. Fixed dimension and `r_n -> r` ensure that replacing `g_n^0` by `g^0` affects the scaled estimator by `o_p(1)`: the coefficient difference tends to zero and multiplies `sqrt(n)(mean_U h-mean_L h)=O_p(1)`.

The labeled centered residual sum and the unlabeled centered control sum are independent. The ordinary iid finite-variance CLT for each, followed by the remainder result, gives

`sqrt(n)(muhat_CF-mu) -> Normal(0,sigma^2)`,

where

`sigma^2 = Var(Y-g^0(S)) + r Var(g^0(S))`

`        = Var(Y) - v/(1+r)`.

At each finite ratio, the fixed comparator has exact variance

`Var(mutilde_n) = [Var(Y)-v/(1+r_n)]/n`.

The crossfit estimator only shares its **first-order asymptotic law**, not necessarily its exact variance or any finite-sample optimality property. Convergence in probability and distribution alone does not establish convergence of actual finite-sample variances without suitable uniform integrability.

If `m(S)` belongs to the affine span of `h`, then `v=Var(m)` and the limiting variance equals A's score-class oracle minimum at the limiting ratio. The relevant condition is representation including the intercept; an approximation is not exact containment.

### 4.5 Consistency of the proposed variance estimator

For observation `i` in fold `k(i)`, define

`R_i=Y_i-g_-k(i)(S_i)`,

and, for each unlabeled observation,

`H_j=sum_k w_k g_-k(T_j)`.

The estimator proposed in B is

`Vhat = s_R^2/n + s_H^2/N`,

where each sample variance is centered by its **own global sample mean** and uses its sample-size-minus-one denominator. This is the correct asymptotic construction.

To verify it despite dependent fitted residuals, compare them with the fixed residuals `R_i^0=Y_i-g^0(S_i)`. Since `h` is bounded and there are fixed finitely many consistent coefficients,

`max_i |R_i-R_i^0| = o_p(1)`.

Likewise `max_j |H_j-g^0(T_j)|=o_p(1)`. Empirical first and second moments of the fixed variables obey the law of large numbers. The cross terms are bounded by Cauchy–Schwarz and the fixed variables' tight empirical second moments. Hence

`s_R^2 -> Var(Y-g^0(S))`,

`s_H^2 -> Var(g^0(S))`,

and `n Vhat -> sigma^2` in probability.

The out-of-fold residuals need not be iid, and `Vhat` need not be unbiased at finite n. The comparison proof, not a residual-iid assertion, establishes consistency. No regression degrees-of-freedom correction is needed for this asymptotic statement; this does not identify `ddof=1` as a finite-sample unbiasedness correction for fitted residuals.

**Unlabeled reuse is crucial:** the unlabeled component is the variance of the **weighted sum control evaluated on the same U sample**. It is not `sum_k w_k^2 s_U^2(g_-k)/N` without covariances. If all fold controls equal the same nonconstant `g` and weights are `1/K`, that erroneous expression is `s_U^2(g)/(KN)`, whereas the correct term is `s_U^2(g)/N`.

### 4.6 Safe CI conclusion and its limitations

If `sigma^2>0`, Slutsky's theorem gives

`(muhat_CF-mu)/sqrt(Vhat) -> Normal(0,1)`.

Therefore the usual two-sided normal interval has **pointwise asymptotic** coverage `1-alpha` for this fixed law and fixed feature specification. In the projection setting, `sigma^2 >= r Var(Y)/(1+r)`, so nonconstant `Y` suffices for positivity.

This does not prove finite-sample coverage, uniform coverage over rare-event sequences, actual finite-n variance convergence, or realized-width dominance. It does not extend automatically to growing bases, data-learned feature maps, distribution shift, observation-dependent folds, singular population feature covariance, or ratio limits zero/infinity. A constant outcome requires separate treatment rather than this nondegenerate normal pivot.

## 5. Claim C: finite-dictionary theorem — PROVED after explicit domains

Assume `n,N>=2`, `alpha in (0,1)`, `0<=Y<=1`, `0<=S<=1`, independent iid samples with a common score law, and a deterministic frozen dictionary at deterministic budgets. Put `a=1/(1+n/N)` and use the five listed controls.

### 5.1 Range constants

Every nonzero dictionary function lies in `[0,a]`:

- `aS`, `a(1-S)`, `a(2S-1)^2`, and `a 1{S>1/2}` all do so.
- Therefore `Y-g(S)` lies in `[-a,1]`, with safe known range length `1+a`.
- `g(T)` has safe known range length `a`.
- For the zero control the residual is `Y`, range length `1`, and its unlabeled contribution is identically zero.

These are worst-case support bounds; no unproved favorable correlation between `Y` and `S` is used. The step threshold and strictness at `1/2` have no adverse effect on boundedness. The bounds remain valid even if some dictionary functions coincide under a particular distribution.

### 5.2 Error allocation and selection

Let `b` be the radius proved in §6. For each of the four nonzero controls, allocate `delta=alpha/(2K)` to each of the two component deviations, with `K=5`. For zero allocate `alpha/K` to the labeled mean and no error to the known-zero unlabeled component.

On the intersection of these component events, for every dictionary member,

`|muhat_g-mu| <= b(residual_g,delta_L,R_L) + b(control_U,delta_U,R_U)`,

with the zero-control second term absent. There are eight nonzero component events plus the zero-control event, and the sum of the assigned failure probabilities is

`8 alpha/(2K) + alpha/K = alpha`.

A union bound gives simultaneous coverage at least `1-alpha`. This bound requires no independence across dictionary entries, nor between the selection rule and the intervals. Intersecting each confidence set with `[0,1]` preserves containment because `mu` lies in that set. Consequently **any measurable selection among these simultaneous sets**, in particular the shortest with fixed tie-breaking, has coverage at least `1-alpha`.

Clipping can produce an empty set on a failure event. That does not invalidate coverage. Define its length as zero if empty sets are allowed; if an implementation demands a nonempty interval, replace an empty set by `[0,1]` before selection. This replacement cannot reduce simultaneous coverage.

The actual logarithms are `log(8K/alpha)` for nonzero-control components and `log(4K/alpha)` for the zero control. Observed zero empirical variance does **not** justify discarding the positive range term. For example, two iid Bernoulli(0.1) observations are both zero with probability `0.81`; a zero-radius mean interval on that event misses the true mean `0.1`. Only a known population-constant variable has the exact zero-range exception.

### 5.3 Comparison claims

The minimum-length selection is no longer than its zero-control candidate on every dataset, but that candidate uses labeled-only EB at level `alpha/K`, **not** the standalone labeled-only EB interval at level `alpha`. No width/coverage dominance over labeled EB at its own alpha, or over binary Clopper–Pearson at its own alpha, follows. The clean statement's disclaimer is correct.

A singleton dictionary containing unscaled `g(S)=S` has residual range `2` and control range `1`, and may allocate `alpha/2` to each component. That is a valid special case of the mechanism. Clopper–Pearson is applicable only for binary outcomes, as the statement notes.

The deterministic-dictionary condition is sufficient. A dictionary frozen independently of both estimation samples also works by conditioning. Choosing transformations or thresholds from these same observed scores is outside this elementary finite-dictionary proof unless an additional argument supplies simultaneous validity for that choice.

## 6. Self-contained proof of the empirical-Bernstein radius

This section proves the mathematical radius in the clean statement, without relying on the cited theorem or its provenance.

Let `Z_1,...,Z_k` be iid with support in an interval of known length `R`, `k>=2`. Write `mu_Z=E[Z]`, `sigma_Z^2=Var(Z)`, and

`s^2 = sum_i (Z_i-mean Z)^2/(k-1)`.

For `delta in (0,1)`, put `L=log(4/delta)`. We prove

`P{ |mean Z-mu_Z| <= sqrt(2 s^2 L/k) + 7 R L/[3(k-1)] } >= 1-delta`.

For `R=0`, every observation equals its known population mean, so exact radius zero is valid. Below assume `R>0`.

### 6.1 Mean concentration using true variance

For a centered variable `X` with `|X|<=R` and variance `sigma_Z^2`, expansion of the exponential and `j!>=2*3^(j-2)` for `j>=2` give, for `0<=t<3/R`,

`log E exp(tX) <= sigma_Z^2 t^2 / [2(1-tR/3)]`.

Indeed `E[X^j]<=E[|X|^j]<=R^(j-2) sigma_Z^2`, and `log(1+x)<=x`. The same bound applies to `-X`.

Independence gives the corresponding mean bound with variance parameter `sigma_Z^2/k` and scale `R/(3k)`. If a variable has log-MGF at most `v t^2/[2(1-c t)]`, substituting

`t=sqrt(2L/v)/(1+c sqrt(2L/v))`

in Chernoff's inequality yields upper-tail threshold `sqrt(2vL)+cL`. Apply this to each sign of the mean (the zero-variance case is immediate). Except on a set of probability at most `2 exp(-L)`,

`|mean Z-mu_Z| <= sigma_Z sqrt(2L/k) + R L/(3k)`.

### 6.2 Lower-tail concentration of the unbiased sample variance

Let `ell=floor(k/2)` and `W=(Z-Z')^2/2` for independent copies. Then

`0<=W<=R^2/2 = M`, and `E[W]=sigma_Z^2`.

For any nonnegative bounded `W` and `t>=0`, `exp(-tW)<=1-tW+t^2 W^2/2` gives

`log E exp(t(E[W]-W)) <= t^2 E[W^2]/2 <= t^2 M E[W]/2`.

Randomly permute the `k` observations and pair the first `2 ell` of them. Let `H_pi` be the average of the `ell` resulting values of `W`. Its conditional average over permutations equals the full order-two U-statistic

`E_pi[H_pi | Z_1,...,Z_k] = [1/(k(k-1))] sum_{i<j}(Z_i-Z_j)^2 = s^2`.

Jensen's inequality applied to the exponential, followed by independence of disjoint pairs for each fixed permutation, gives

`E exp(t(sigma_Z^2-s^2)) <= exp(t^2 M sigma_Z^2/(2 ell))`.

Chernoff optimization therefore gives, with failure probability at most `exp(-L)`,

`sigma_Z^2-s^2 <= R sigma_Z sqrt(L/ell)`.

Putting `d=R sqrt(L/ell)`, this inequality implies

`sigma_Z <= [d+sqrt(d^2+4s^2)]/2 <= s+d`.

If `sigma_Z=0`, the same conclusion is deterministic.

### 6.3 Combining the events and checking the constant

On the mean event and the sample-variance event,

`|mean Z-mu_Z| <= sqrt(2s^2 L/k) + R L sqrt(2/(k ell)) + R L/(3k)`.

Since `ell>= (k-1)/2`,

`sqrt(2/(k ell)) <= 2/sqrt(k(k-1)) <= 2/(k-1)`.

Also `1/(3k)<=1/[3(k-1)]`. The last two terms are thus at most

`(2+1/3) R L/(k-1) = 7 R L/[3(k-1)]`.

The union failure probability is at most `3 exp(-L)=3delta/4<=delta`. This proves the advertised two-sided radius, including its unbiased sample-variance convention and its `7/3` range constant. This derivation establishes mathematical validity; it makes no claim to have verified the cited paper's theorem numbering.

## 7. Synthetic moment audit

With `S~Uniform[0,1]`, `Var(S)=1/12`. Means, `Var(m)`, and score covariances follow from `m` alone. To obtain the listed outcome variances, **add** `Y|S~Bernoulli(m(S))`. Under that added law:

| Model | `mu` | `Var(Y)` | `Var(m)` | `Cov(Y,S)` |
|---|---:|---:|---:|---:|
| `0.1+0.8S` | `0.5` | `0.25` | `0.64/12` | `0.8/12` |
| `0.02+0.96(2S-1)^2` | `0.34` | `0.2244` | `0.08192` | `0` |
| `0.01+0.98 1{S>0.5}` | `0.5` | `0.25` | `0.2401` | `0.1225` |
| Constant `0.5` | `0.5` | `0.25` | `0` | `0` |
| Constant `0.01` | `0.01` | `0.0099` | `0` | `0` |

Verification:

- Linear: the nonconstant part has variance `0.8^2 Var(S)` and covariance `0.8 Var(S)`.
- Quadratic: `U=2S-1` is uniform on `[-1,1]`; `E[U^2]=1/3`, `E[U^4]=1/5`, so `Var(m)=0.96^2(1/5-1/9)=0.08192`. Symmetry makes `Cov(S,U^2)=0`.
- Step: `P(S>1/2)=1/2` and `E[S 1{S>1/2}]=3/8`; hence `Cov(S,1{S>1/2})=1/8` and the displayed step covariance follows.
- Bernoulli marginal variance is `mu(1-mu)`. Without the added binary law, replace it by `Var(m)+E[Var(Y|S)]`.

The corresponding **nonlinear-over-scalar oracle variance advantages**, stated as scalar variance minus full score-oracle variance, are:

- Linear: zero, with `lambda*=0.8/(1+r)`.
- Quadratic: `0.08192/[n(1+r)]`, with scalar `lambda*=0`.
- Step: `0.060025/[n(1+r)]`, since `Cov(Y,S)^2/Var(S)=0.180075`; scalar `lambda*=1.47/(1+r)`.
- Null and rare constants: zero oracle gain over no predictions.

Thus the step model does not have zero scalar signal; the quadratic model does. The rare constant model has no oracle control gain but can still create nonuniform small-sample normal-approximation difficulties. A fixed success probability `0.01` and a sequence tending to zero are different asymptotic settings.

## 8. Safe theorem wording for reuse

### A — exact oracle variance theorem

> For independent iid labeled and unlabeled samples at deterministic positive budgets with a common score law and `Y in L2`, and every deterministic square-integrable score control, the estimator is unbiased and satisfies the displayed centered-square variance identity. Its minimum over this additive score-measurable class is attained by `E[Y|S]/(1+n/N)` modulo constants. For a square-integrable nonconstant scalar score, the displayed scalar optimum and gap hold; scalar/full-oracle equality occurs exactly when the conditional mean is affine in the score almost surely. Full-oracle gain is zero exactly when that conditional mean is constant. These are variance statements within the specified class, not CI or universal-estimator optimality statements.

### B — pointwise asymptotic crossfit CI theorem

> Fix a bounded finite-dimensional feature vector with positive definite population covariance, a fixed distribution with finite second outcome moment, independent iid labeled/unlabeled samples with a common score law, and a fixed number of observation-independent folds whose deterministic sizes and training-complement sizes are proportional to n. With exact fold-size weights, a finite positive limiting labeled/unlabeled ratio, and training-only foldwise coefficients converging in probability to the population regression coefficients with intercept, the crossfit estimator is first-order equivalent to the deterministic projection control. The proposed `Vhat=s_R^2/n+s_H^2/N`, using globally centered out-of-fold residuals and the weighted sum control on the reused unlabeled sample, satisfies `n Vhat -> sigma^2` in probability. If `sigma^2>0`, the normal interval has pointwise asymptotic coverage `1-alpha`. Vanishing ridge suffices for coefficient consistency under the specified bounded penalty normalization; epsilon of order at most n-inverse-square-root ensures the sharper root-n coefficient and order-n-inverse remainder rates, as satisfied by `1e-4/n`. No finite-sample coverage or width dominance is asserted.

### C — finite-sample simultaneous selection theorem

> For `0<=Y<=1`, `0<=S<=1`, independent iid samples with a common score law, `n,N>=2`, `alpha in (0,1)`, and the specified deterministic five-control dictionary with `a=1/(1+n/N)` and `K=5`, use the empirical-Bernstein radius with residual range `1+a` and control range `a` for nonzero controls, allocating `alpha/(2K)` per component. For the zero control use labeled range `1`, error `alpha/K`, and no unlabeled radius. All intervals clipped to `[0,1]` cover simultaneously with probability at least `1-alpha`; therefore selecting the shortest has finite-sample coverage at least `1-alpha`. No independence across candidates is needed. No width dominance over standalone level-alpha labeled intervals or binary exact intervals is asserted.

### Synthetic setup

> Generate `S~Uniform[0,1]` and `Y|S~Bernoulli(m(S))` for each listed regression function. Then all displayed moments hold. If only the regression function is specified, the means, regression variances, and score covariances hold, but the outcome variances remain unspecified.

## Proof / Report

Sections 2–8 give exact counterexamples, clean proofs, dependence checks, and replacement theorem statements. No original claim is silently promoted from an asymptotic statement to a finite-sample theorem. Claim C's concentration ingredient is proved internally rather than accepted from a citation.

## Audit

- audits-run: Counterexample-first audit; centered-projection calculation; exact crossfit remainder and variance-consistency check; reused-unlabeled covariance check; self-contained concentration/range/budget proof; analytic moment checks; final boundary/quantifier pass.
- critical-issues: Observation-dependent folds can invalidate B. Merely vanishing ridge invalidates its stated intermediate rates. Synthetic outcome variances require an additional law.
- remaining-gaps: No unresolved mathematical gap in the repaired statements above. The original ridge wording does not uniquely define an objective; the theorem specifies a sufficient normalization instead. No paper attribution or implementation behavior has been certified.

## Proof Artifact

- verified claims: A and its equality/no-gain cases; repaired pointwise B including studentization and unlabeled reuse; C with explicit domains and a self-contained empirical-Bernstein proof; all synthetic moments under an explicit binary outcome law.
- negative attempts: No counterexample to A or C under their explicit domains. Treating overlapping fitted residuals or reused unlabeled fold means as independent is unnecessary and would be an invalid proof shortcut.

## Reflection

- successful-pattern: Write the exact weighted remainder before invoking crossfit intuition; prove concentration premises rather than relying on their citation.
- failed-pattern-to-avoid: Balance is not independence, consistency is not a root-n rate, and a conditional mean is not a full outcome distribution.
- memory-persisted: false
- storage-location: `/work/artifacts/theory_audit.md`; compact process notes in `/work/artifacts/theory_audit_worklog.md`.
- proposed-memory-updates: none; no profile inference and no task-specific findings written to persistent memory.
