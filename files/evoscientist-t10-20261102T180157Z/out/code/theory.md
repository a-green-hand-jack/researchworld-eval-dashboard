# Clean theoretical claims for independent audit

Let iid labeled (Y_i,S_i), i=1..n, and independent iid scores T_j, j=1..N, share a common law for S; Y in L2; f frozen independently of both samples. Fix r=n/N>0 and deterministic g in L2(P_S). Define muhat_g=mean_L[Y-g(S)]+mean_U[g(T)]. Constants in g cancel.

Claim A: unbiasedness and V(g)=[VarY-2Cov(Y,g)+(1+r)Var(g)]/n. Writing m(S)=E[Y|S],
V(g)=VarY/n - Var(m)/[n(1+r)] + (1+r)/n Var(g-m/(1+r)).
Thus oracle g*=m/(1+r)+constant. Within this score-measurable additive-rectification class the optimum is attained, and for scalar g=lambda S, VarS>0,
lambda*=Cov(Y,S)/[(1+r)VarS].
Gap V(lambda*S)-V(g*) = [Var(m)-Cov(Y,S)^2/VarS]/[n(1+r)]. Equality iff m is affine in S almost surely. Constant S: gap0 because m constant. Oracle gain over no predictions zero iff m constant. These are oracle variance statements, not finite-sample intervals, not lower bounds over all possible estimators or over full features X.

Proof: expand independent means; replace Cov(Y,g) by Cov(m,g) via conditional expectation; complete centered square. Cauchy-Schwarz/projection gives nonnegative gap and equality. For constant S all g constant. Affine transformations aS+b (a nonzero) do not change optimally scalar-tuned variance.

Claim B (asymptotic only): choose a fixed finite-dimensional bounded feature vector h(S). On each of fixed K balanced folds, train ridge regression with intercept of Y on h using other labeled folds, ridge penalty epsilon_n times empirical covariance, epsilon_n->0 (implementation epsilon=1e-6 fixed is a practically negligible but NONZERO asymptotic shrinkage; use epsilon_n=1e-4/n instead so it vanishes). Define b_-k, g_-k(s)=b_-k^T h(s)/(1+r), intercept omitted because cancels. Estimator meanY + sum_k w_k[mean_U g_-k - mean_Lk g_-k], w_k=n_k/n. With nonsingular limiting feature covariance, n,N->infty and n/N->r in(0,infty), b_-k converge to linear L2 projection coefficients. Conditional moment differences are O_p(n^-1/2); finite p regression errors O_p(n^-1/2), product O_p(n^-1). Hence first-order equivalent to fixed oracle projection control. Estimate variance using sample variance of out-of-fold residuals /n plus sample variance_U of sum_k w_k g_-k /N. Center each variance by its global sample mean, no degrees-of-freedom beyond ddof1. Consistency follows bounded features and coefficients convergence. CLT requires strictly positive limiting nV. If basis contains m, attain A's score-class minimum. Claim not applicable to tiny n, singular design, unbounded growing basis, distribution shift, degenerate rare-label sequence, or ratio limit0/infty without further argument.

Claim C finite-sample bound: Assume 0<=Y<=1,0<=S<=1. Fixed dictionary G={0,aS,a(1-S),a(2S-1)^2,a 1{S>.5}}, a=1/(1+r), K=5. For bounded iid Z of known range length R and k>=2, two-sided empirical Bernstein radius b(Z,delta,R)=sqrt[2 s_Z² log(4/delta)/k]+7R log(4/delta)/[3(k-1)] by two applications of Maurer/Pontil2009 Theorem4, s² unbiased sample variance. A zero-range constant variable has exact zero error, radius0.
For each nonzero g assign delta=alpha/(2K) to each labeled residual and unlabeled mean, and radii with range lengths 1+a and a, respectively. g=0 uses delta=alpha/K for labels and no U error. Then I_g centered at muhat_g with sum of these radii, intersected with[0,1], is valid jointly for all g with probability>=1-alpha. Select the shortest I_g, tie break fixed dictionary order. This selection has finite-sample coverage>=1-alpha for all such joint laws; no independence across g needed. Dictionary may depend on deterministic n,N but must not depend on labels or observed scores. Uses same frozen observations and no sample split. Its coverage may be extremely conservative. Not a proof of dominance over CP or EB_labeled at their own alpha; logK and residual range can cause larger width. Applying no multiplicity correction is not justified.

Proof C: each nonzero interval fails with probability<=alpha/K by union over its two components, zero control likewise; union over K then selection. Truncation to [0,1] preserves containment of true mu. K=1,g=S recovers EB_PPI with alpha/2 each and range2,1 (without a scaling). EB labeled alone uses alpha. CP uses exact equal-tail binomial interval for binary Y.

Synthetic moments (S uniform[0,1]):
linear m=.1+.8S: mu=.5, VarY=.25, Var(m)=.64/12, Cov(Y,S)=.8/12.
quadratic m=.02+.96(2S-1)^2: mu=.34, VarY=.2244, Var(m)=.96²*(1/5-1/9)=.08192, Cov(Y,S)=0.
step m=.01+.98 1{S>.5}: mu=.5, VarY=.25, Var(m)=.98²/4=.2401, Cov(Y,S)=.98/8=.1225.
null m=.5 and rare m=.01: m constant, Cov0, Var(m)0.
