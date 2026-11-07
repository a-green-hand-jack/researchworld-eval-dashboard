# `replicates.parquet` columns
experiment, tag (cell label inside the experiment), graph (er/sbm/ba/ws/geo/fb_ego/fb_stanford), graph_id (graph redraw index; always 0 for real graphs),
n, mean_degree, mechanism (M1 linear in neighbour fraction; M3 concave saturation g(f)=(1-e^{-3f})/(1-e^{-3}); M4 = M1 + 2-hop term; M5 = M1 with degree-dependent
gamma_i = gamma(1+0.5 z_deg); others by outcome kind: pow, thresh, lin_count), rho (= gamma/tau, interference-to-direct), sigma (SD of fresh measurement noise),
design (bernoulli / cluster), p, cluster_res (Louvain resolution; NA for Bernoulli), graph_error_rate (fraction of edges dropped and re-added at random in the
graph used for features), estimator (dm, hajek [strict full-neighbourhood exposure], hajek_q0.75, ols_f, ols_cnt, ols_cnt_adj, ols_f_adj, ols_f_deg, ols_f2, ols_poly, ols_poly3, ridge_rich, gbm),
fit_data ("observed": fit to (z, y); "population": fit to the noise- and baseline-free signal m(z): isolates the approximation error), seed (cell id; see README),
rep, tau_true (exact GATE from m(1)-m(0)), tau_hat (NaN if undefined, e.g. no unit with fully treated neighbourhood), ci_lo/ci_hi (95% normal interval from the
cluster-robust (Louvain communities) sandwich variance; only for OLS estimators in cells with se=true; NaN otherwise), f_mean/f_sd/overlap_treated/overlap_control
(exposure-support statistics of the realised assignment: mean and SD of the neighbour fraction f, share of units with f>=0.9 / f<=0.1), theory_sd (P2 prediction, Bernoulli only; NaN if not computed).
