# Analysis plan, written before the main simulations

This is an autonomous, CPU-only diagnostic study, not a preregistered clinical
or field experiment. Master seed 20261102. No broad literature search is used.

Hypotheses to test:
1. For correctly specified linear interference, conditional endpoint weight
   variance predicts empirical squared error. Degree concentration increases
   that variance; sample size helps only relative to the relevant degree scale.
2. Increasing polynomial order can correct approximation bias but sharply
   increase endpoint variance. Prediction-based selection need not select the
   best GATE model.
3. Linear regression can recover the quadratic GATE at saturation 1/2 through
   symmetry despite nonlinear response; changing saturation breaks this.
4. Graph cluster assignment can improve exposure support but is not uniformly
   superior. Its effect depends on graph partition and response form.
5. Correct noise covariance repairs intervals only for correct response models;
   it does not repair extrapolation bias or rare threshold activation.

Primary graphs: three regular graphs (1600 vertices, degree 8/32/128), a
40-block planted SBM (40 vertices per block, within probability .6, between
4/1560), a BA graph (1600, m=16), and the full public SNAP ego-Facebook graph.
Each graph is fixed, with independent assignments and noise over repetitions.
All primary mean-response GATEs equal 3, with five response laws (linear,
quadratic, cubic, threshold at .8, and two-hop). Primary outcomes: bias, RMSE,
Monte Carlo standard error, and coverage; paired comparisons share noise.

Methods: difference in means, nested OLS exposure regressions (linear,
quadratic, cubic, two-hop), fixed-penalty cubic ridge, closed-neighborhood HT.
HT is not valid for the two-hop law and finite Monte Carlo cannot resolve its
rare tails; both issues must be prominently reported.

Planned repetitions: main 400; correlated-noise 400; scaling 400; validation
150; saturation 400. Scaling adds n=800/3200 for each degree. Validation uses
node-held-out outcome prediction on cubic law and includes random forest as
an interpolation-oriented comparator. Selection uses OLS L/Q/C only.
Any changes or failed runs will be logged in RUN_LOG.md.

The study has no access to actual platform treatment/outcome data. Its novel
claim is limited to an integrated diagnostic/sensitivity analysis and controlled
evidence, not invention of regression adjustment or a universal optimal method.
