# Exact two-stratum binomial interval: clean proof and scope

Let Y be binary, S any frozen scalar score. Let A=1{S>.5}, p=P(A=1), q_h=P(Y=1|A=h); arbitrary q_h in[0,1] if P(A=h)=0. mu=(1-p)q0+pq1. Assume iid labeled rows (Y_i,S_i), independent iid unlabeled scores T_j, all same S marginal. Folds or fitting not used.

Let C(q_h) be equal-tail Clopper-Pearson with error alpha/3 from the labeled rows with A=h, and [0,1] if stratum count0. Conditional on the labeled membership vector A_1..A_n, the labels in stratum h are independent Bernoulli(q_h); the CP event fails conditionally with probability <=alpha/3. Integrating memberships proves unconditional failure <=alpha/3, regardless of random counts.

Let C(p) be CP with error alpha/3 from all n+N score memberships. These memberships are iid Bernoulli(p), so P(p notin C(p))<=alpha/3. It is dependent on C(q_h), which is harmless: union bound gives all3 contain true values with probability>=1-alpha. The q intervals and p intervals can reuse scores without assuming independence of the resulting intervals.

For C(p)=[pL,pU], C(qh)=[lh,uh], the image of this confidence rectangle under F(p,q0,q1)=(1-p)q0+pq1 is covered by [L,U], where L=min_{t in{pL,pU}}[(1-t)l0+t l1] and U=max_{t in{pL,pU}}[(1-t)u0+t u1]. For each fixed p the map is nondecreasing in both q's; after choosing q endpoints it is affine in p so extrema occur at p endpoints. Therefore the returned interval contains mu with probability>=1-alpha. This is a construction from standard binomial inversion plus union bound; not a claim of a new stratification technique or global optimality.

CP inversion justification: for a binomial K~Bin(m,q), exclude q when either its upper-tail or lower-tail test pvalue is below delta/2. Each rejection tail has probability<=delta/2 by monotonic binomial tail quantiles, so coverage>=1-delta; inversion yields beta quantile formulas in exact_stratified.py. Discreteness can make coverage strictly greater. Boundary q=0 or1 handled by the zero/all-success endpoints; empty m=0 returns[0,1].

Limitations: binary outcomes only in this implementation; fixed threshold not label-selected; scores/labels from same population; no claim valid under label shift; no uniform dominance over unstratified CP. If using more candidate partitions, require simultaneous correction or an independent selection sample. At N/n finite, the score mass p must not be treated as known. The code includes its uncertainty using pooled n+N scores.

Numerical check (not proof): tests/test_stratified.py enumerates all labeled4-category count vectors for n6 and all unlabeled stratum counts for N8 at p=.3,q0=.1,q1=.9, checking probability sums to1 and coverage>=.95. The analytic proof above provides the actual distribution-free guarantee.
