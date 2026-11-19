# Main-run freeze

Following story-repo#2 scope decision (2026-11-02), the confirmatory matrix is fixed before execution:

- Replication indices 1000..1099, RNG seeds 901000..901099; coefficient seeds 1729+K. Pilot indices 0/1 excluded.
- K in {3,10}; calibration n in {99,499}; scenarios homogeneous/heterogeneous.
- Seven methods: raw_l2, raw_linf, clr_l2, clr_scaled, clr_mondrian, coord_naive, coord_bonferroni. A weighted-quantile helper is tested but not an additional main method without protocol amendment.
- Alpha .1, training n=1000, 5000 new test observations per iid/shift environment.
- K=3 Euclidean simplex area reference: 32 independent X anchors per replication/environment, 8192 independent uniform compositions per anchor, common candidates across methods.
- Main inference: pointwise 95% t intervals across 100 independent dataset replications, paired method contrasts, and paired iid-to-shift contrasts. Descriptive run-level finite-test coverage diagnostics include 10/50/90 percentiles and fraction below .85, with binomial Wilson intervals for that empirical fraction.
- Infinite regions remain in coverage and area. Omit mean radius for any affected cell. No cross-geometry K=10 efficiency ranking.

Focused sensitivity cells and seeds will be recorded separately before execution. Any main area contrast too close to MC resolution will receive a paired higher-candidate diagnostic or have its ordering withheld.
