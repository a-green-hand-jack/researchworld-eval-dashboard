# Final theory audit

## Verdicts and remaining gaps

**Complement-symmetry proof: SOUND on a positive-probability full-rank event.** No transpose, weight, or quadratic-bias sign error was found. **Theory repairs: PARTIAL.** The incorrect necessity claim about mean specification is repaired; several domain/conditioning qualifications requested by the earlier audit remain unstated.

| Location | Verdict | Finding / minimal repair |
|---|---|---|
| `symmetry_claim.md`, matrix transformation | **SOUND** | The relevant transform of the contrast is inverse transpose, not inverse. The displayed proof uses it correctly. |
| Symmetry, rank conditioning | **SOUND with domain GAP** | Complementation preserves rank and the accepted law's symmetry. Explicitly require `Pr(R)>0`; some allowed graphs have `R` empty. |
| Symmetry, weight constraints and quadratic bias | **SOUND** | Constraints imply `b(z)=w(z)'s(z)^2−1` and `b(1−z)=−b(z)`. Squares here are componentwise. |
| Symmetry, noisy unbiasedness at `.5` | **SOUND** | Independent integrable mean-zero noise suffices as stated. In fact, odd weights also give design-unbiasedness for each fixed shared additive error schedule; see below. |
| `theory.md`, setting and Claims 1–2 | **SOUND** | Endpoint noise cancellation, OLS decomposition, conditional MSE, and residual bound are correct. Positive acceptance probability should be stated explicitly. |
| Theory, known-covariance intervals | **SOUND; REPAIRED** | Zero conditional contrast bias is now sufficient; full mean specification is explicitly not necessary. Exact Gaussian quantile and positive variance are correctly specified. |
| Theory, ridge | **GAP: domain not fully repaired** | Declare symmetric PSD `D_pen`, `lambda>=0`, and existence of the inverse; distinguish it from `D_noise`. Direct bias–variance identities are sound whenever the displayed weights exist. |
| Theory, Claim 3 | **SOUND; scope warning remains useful** | Lower bounds concern estimators actually defined on the common observed support, not an unavailable singular additive OLS output. |
| Theory, Claim 4 | **SOUND unconditionally; conditioning repair not explicit** | Still lacks an express warning against reuse after rank filtering. Use the conditional law or the acceptance-adjusted bound below. |
| Theory, heuristic | **SOUND only as labeled heuristic** | Proxy `4(1+d)/n` is correct; no inverse-Gram concentration or general guarantee is proved or claimed. |
| Theory, covariance | **SOUND with graph-domain GAP** | Transpose/order are correct. Explicitly restrict the degree formulas to simple unweighted loop-free positive-degree graphs, or supply alternate conventions. |

These are local domain/scope omissions, not a failure of the complement-pairing argument. The symmetry result does **not** repair the general rank-filtered visibility issue.

## 1. Independent verification of complement symmetry

Let `P 1=1`, `s=Pz`, `X=[1,x,z,s]`, `c=(0,0,1,1)'`, `G=X'X`, and `R={rank X=4}`. The fixed covariate has the same value at both global endpoints, so `m(1)−m(0)=2·1` and `T=2`.

### Matrix transpose

The explicit right-multiplication matrix is

\[
A=\begin{pmatrix}
1&0&1&1\\
0&1&0&0\\
0&0&-1&0\\
0&0&0&-1
\end{pmatrix}.
\]

Then `X(1−z)=X(z)A`, `A²=I`, and `A'c=−c`. In particular, `Ac=(2,0,−1,−1)'` is **not** `−c`; confusing these orientations would invalidate the proof, but the source does not do so. On `R`,

\[
\begin{aligned}
w(1-z)
&=XA(A^TGA)^{-1}c\\
&=XG^{-1}A^{-T}c=-XG^{-1}c=-w(z).
\end{aligned}
\]

### Weight constraints and bias

Symmetry of `G` gives `X'w=c`, hence

\[
w^T1=w^Tx=0,\qquad w^Tz=w^Ts=1.
\]

Consequently, writing `q=w^T(s^{\circ2})`,

\[
b(z)=w^Tm(z)-2=q-1.
\]

At the complement, using the original weights on the right,

\[
\begin{aligned}
b(1-z)
&=-w^T[a1+bx+(1-z)+(1-s)^{\circ2}]-2\\
&=-[-1-2+q]-2=1-q=-b(z).
\end{aligned}
\]

Thus the square's cross term is essential: `w'(1−s)^2=−2+q`, not simply `q`.

### Conditioning and noise

Invertible `A` makes `R` complement-invariant. If `Pr(R)>0` and the original assignment law is complement-symmetric, then for every accepted assignment

\[
\Pr(Z=z\mid R)=\Pr(Z=1-z\mid R).
\]

Pairwise cancellation gives `E[b(Z)|R]=0`. Independence of assignment and integrable mean-zero noise gives `E[w(Z)'epsilon|R]=0`. Therefore

\[
E[\widehat T\mid R]=2.
\]

There is a stronger symmetry-specific observation: `w(1−z)=−w(z)` also gives `E_Z[w(Z)|R]=0`. Consequently, for **each fixed shared additive error schedule** `e`, `E_Z[w(Z)'e|R]=0` and `E_Z[widehat T|R,e]=2` under the same complement-symmetric design. Mean-zero noise is sufficient, not necessary, for this unbiasedness. This does not establish fixed-schedule Gaussian interval coverage.

A finite assignment space makes the accepted deterministic weights and biases bounded for this fixed graph and `n`; moments of the noisy estimate additionally require the corresponding noise moments. There is no bound uniform over graphs or `n` here.

**Nonvacuity gap:** no isolates alone does not ensure `Pr(R)>0`. On `K_n`, with `t=1'z`,

\[
s=\frac{t}{n-1}1-\frac{1}{n-1}z,
\]

so `[1,x,z,s]` is singular for every assignment, whatever fixed `x` is. Conditional unbiasedness is undefined there. Add `Pr(R)>0` to the claim, rather than asserting existence of an accepted estimate on every graph.

Bernoulli(`.5`) and independent fair treatment of fixed clusters satisfy the required joint symmetry; marginal treatment probability `.5` alone is insufficient to establish that symmetry. At `.2/.8` the proof supplies no individual-design unbiasedness conclusion. Nor does it prove conditional unbiasedness at each assignment, small MSE, or valid intervals. In particular, `E[b|R]=0` need not imply `b(z)=0`, so it cannot invoke Theory Claim 1's conditional coverage result.

## 2. Verification of theory repairs

1. **OLS, target, residual bound — SOUND.** With assignment-only features, `w'Phi=c'` and `T=c'beta+Delta r` give exactly the stated error. Independence preserves the error moments given an assignment and under assignment-only rank acceptance. Gaussianity is unnecessary for `b²+v`. The shared endpoint error schedule cancels exactly. Add `Pr(R)>0` for any accepted-law average; the notation `Phi(z)` already indicates assignment-only construction.

2. **Interval necessity error — REPAIRED.** The current text correctly says full mean specification is sufficient, not necessary. With positive variance, exact conditional Gaussian coverage is `.95` at `b(z)=0`; nonzero shifts strictly lower that symmetric interval's conditional coverage. The document no longer asserts the false necessity statement identified in the earlier audit.

3. **Ridge — STILL NEEDS DECLARATIONS.** A safe version specifies symmetric PSD `D_pen` with zero intercept penalty and `lambda>=0`; on a full-rank design this ensures invertibility. More generally the direct `b_lambda²+v_lambda` identity needs only defined assignment-measurable weights. For the conventional symmetric penalty, the omitted OLS cancellation becomes

   \[
   w_\lambda^T\Phi
   =c^T-\lambda c^T(G+\lambda D_{\rm pen})^{-1}D_{\rm pen},
   \]

   agreeing with the current warning. An unpenalized intercept alone neither ensures invertibility for arbitrary penalties nor removes slope shrinkage bias. The current use of `D` for both penalty and noise scaling remains ambiguous.

4. **Support lower bound — SOUND.** For even `n>=4`, balanced `K_n` assignments have `s_i<=2/3<.8`. The two worlds therefore have identical observed laws but targets separated by `delta`. The displayed identity implies maximum MSE at least `delta²/4`; their common estimator expectation implies maximum absolute bias at least `delta/2`. Add the earlier audit's explicit caveat: these statements apply to estimators defined on that support. Additive `(1,z,s)` OLS is always rejected there, not assigned a risk.

5. **Visibility — UNCONDITIONAL CLAIM SOUND; RANK-FILTERING WARNING STILL ABSENT.** Under the product law and positive degree, the binomial tail and union bound are correct without independent neighborhood events. If `V` denotes any threshold exposure and `p_d=Pr[Binomial(d,.5)>=ceil(.8d)]`, the generic accepted-law consequence is only

   \[
   \Pr(V\mid R)\leq\min\{1,np_d/\Pr(R)\},\qquad\Pr(R)>0.
   \]

   Exact stress test from the earlier audit remains valid: on a triangle with sole feature `Phi_i=1{s_i>=.8}`, `R=V`, `p_d=1/4`, and `Pr(R)=1/2`. Then `Pr(V|R)=1`, exceeding the unconditional union bound `3/4`. Assignment–noise independence survives acceptance; product treatment independence generally does not. The existing claim is not false as written under its original product law, but the recommended explicit scope repair was not incorporated.

6. **Graph domains and covariance — ALGEBRA SOUND; ASSUMPTIONS NOT FULLY DECLARED.** For simple unweighted loop-free graphs with `d_i>0`, put `B=D_noise(I+2P)`. Then

   \[
   \Sigma=BB^T,\qquad
   w^T\Sigma w=\|B^Tw\|^2
   =\|D_{\rm noise}w+2P^TD_{\rm noise}w\|^2.
   \]

   Also `Sigma_ii=D_noise,ii²(1+4/d_i)=1`. The transpose cannot be dropped on irregular graphs, and `D_noise` cannot generally commute with `P`. On the three-vertex path, `w=e_1` gives variance `1`; incorrectly using `P` instead of `P'` gives `2/5`. No-isolate and unweighted-neighbor assumptions should be stated where the degree identities are used; weighted graphs require row-squared norms instead of `1/d_i`.

## Audit record

- Scope: the three requested local files, direct algebra, and exact hand-checked examples only. No web, literature, identification search, implementation inspection, code writing, or code execution.
- Plan: audit finite-dimensional probability/linear algebra; separate algebra, accepted-law conditioning, and declaration gaps.
- Independent checks: explicit matrix/constraint derivation; complement pairing; complete-graph zero-acceptance stress test; triangle conditional-visibility stress test; path covariance orientation. Each check reached its stated verdict without numerical approximation.
- Final adversarial check: dimensions, inverse-transpose orientation, endpoint target, quadratic expansion, positive-probability conditioning, error independence, support quantifiers, and coverage-versus-unbiasedness distinction rechecked. No unresolved algebraic flaw in the qualified symmetry theorem. The domain/scope gaps above remain in the source documents.
- Manual validation used for the no-code audit. Named-pattern screening found missing domain declarations, not hidden infinite operations, circularity, or an unexpanded symmetry argument after the explicit derivation above.
- Reflection: preserve symmetries through invariant conditioning, not general product-law properties. No new observation/profile memory persisted; the rank-conditioning lesson already exists in memory.

final-status: HANDED_OFF

The audit is complete; this status records the explicit source-document qualifications still awaiting repair, not an unverified symmetry calculation.
