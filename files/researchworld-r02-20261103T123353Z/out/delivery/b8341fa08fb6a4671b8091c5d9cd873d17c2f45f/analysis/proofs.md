# Supporting derivations and numerical conventions

## Rank coverage

Condition on proper-training data and any independent training-derived randomness. Let S_1,...,S_n,S_(n+1) be exchangeable scalar calibration/new scores, and k=ceil((n+1)(1-alpha)). Give ties an independent random ordering conceptually: the new observation's rank is uniform on 1,...,n+1. If k<=n, the event new rank<=k implies S_(n+1)<=the kth calibration score. Thus P(coverage)>=k/(n+1)>=1-alpha. Ties included with <= can only enlarge coverage. If k=n+1, q=+infinity and coverage is 1. Under distinct scores the implication is an equivalence and coverage=k/(n+1). Intersecting a set with the simplex changes no event because the actual target lies in the simplex. This is a marginal statement over calibration and new data, conditional on the independent training fit; it need not hold conditional on the realized calibration sample or each X.

For fixed X-observable group g, exchangeability conditional on group membership gives the same result at its realized calibration size n_g and an independent test observation in that group. Empty/small groups use infinity rather than an estimated finite quantile without enough ranks. A fixed training-derived positive scale or deterministic zero transform preserves exchangeability of the score, so the same proof applies. This does not assert pointwise conditional validity or shifted-test validity.

For coordinate j, finite-sample calibration at alpha/K gives P(Y_j outside interval_j)<=alpha/K. The union bound gives P(any component outside)<=sum_j alpha/K=alpha. Intersect with the simplex unchanged. Using alpha separately per component provides only the bound K alpha and no joint 1-alpha guarantee.

## Calibration variability diagnostic

For iid scores with a continuous conditional CDF F after conditioning on the training fit, F(S_i) are iid Uniform(0,1). For k<=n, the conditional true coverage of the kth-score set is F(S_(k))~Beta(k,n+1-k). Its mean is k/(n+1) and variance k(n+1-k)/((n+1)^2(n+2)). With m independent test points, empirical coverage adds conditional binomial noise: Var(C_hat)=Var(P)+E[P(1-P)]/m. The diagnostic generates Uniform calibration scores, actual finite-rank thresholds and independent binomial test counts, checks both moments and the distribution, and saves all draws. It is an implementation check, not evidence of a new theorem.

## Common-volume integration

Let d=K-1 and B be an orthonormal K by d contrast matrix. Simplex Hausdorff volume is sqrt(K)/d!. An ordinary tangent-space L2 ball has volume V_d r^d, V_d=pi^(d/2)/Gamma(d/2+1); rejection of points outside the simplex multiplies it by the in-simplex fraction.

For w=softmax(Bz), the tangent Jacobian is K prod_j w_j. This follows because at y=(1/K,...,1/K), the derivative has all d singular values 1/K, and more generally the product of the nonzero eigenvalues of diag(w)-ww^T is K prod w. Normalized simplex volume of an ILR ball is sqrt(K)d! V_d r^d E[prod w], for z uniform on that ball. For the smoothed score, w=T_epsilon(y); original y=(1+K epsilon)w-epsilon, whose tangent-space Jacobian is (1+K epsilon)^d. Multiply by this factor and retain only w_j>=epsilon/(1+K epsilon). This computes volume for the inverse-image region on original Y.

For s=sqrt(y), s lies on the unit sphere in the positive orthant. Hellinger distance<=r means s dot sqrt(center)>=1-r^2. The sphere-to-simplex Jacobian is 2^d sqrt(K)prod s_j, hence normalized Jacobian is 2^d d!prod s. Sample uniformly in that spherical cap, reject negative coordinates and integrate the Jacobian times cap area. For r>=1 the whole simplex is covered. Truncated angular sampling uses sin^2(theta)~Beta(d/2,1/2) truncated at 1-(1-r^2)^2. Coordinate boxes are integrated in the first d barycentric coordinates; normalized volume is d! times ordinary coordinate-chart volume.

The log-ratio Jacobian initially omitted a sqrt(K) normalization in a working implementation. An independent direct-simplex integration test caught it before the pilot; it was corrected. No confirmatory result used the incorrect implementation. Current tests compare both interior and near-boundary centers and smoothed inverse-image regions to independently generated uniform-simplex integration.

## Declared group-prevalence shift

The stress arm changes only P(G=1) from .1 to .4 and holds the distribution of (other X,Y)|G fixed. Global calibration can lose marginal coverage because the poorly covered minority receives more weight. The fixed-group/Mondrian guarantee survives this particular shift: if for each g its new-data coverage is >=1-alpha (averaged over within-group calibration sampling at realized n_g), any test mixture weights sum those lower bounds to >=1-alpha. This requires invariant within-group laws and does not cover arbitrary covariate shift inside a group or response shift. Thus the stress arm tests both a known limitation of global calibration and the precisely scoped protection supplied by fixed-group calibration.

TV uses ||y-center||_1/2. Its sublevel set is convex and can be intersected with the simplex without changing the target event. TV<=r implies |y_j-center_j|<=r because the positive coordinate differences sum to TV, as do the magnitudes of negative differences. Thus a product of componentwise bounds in the first K-1 barycentric coordinates is a valid integration proposal. For K=3 an interior TV ball is a hexagon of normalized area 6r^2; this supplies an additional independent analytic integration check.
