> SUPERSEDED V1: retained provenance only. See exposure_boundary_correction.md; do not use as corrected-study evidence.

# Final completed-study evidence and claim map

Scope: all 102 planned cells, R400, 2,937,600 estimator-output rows; 36 fixed graph instances, including five independent draws for each of seven synthetic regimes and one full SNAP graph. Core/noise/imbalance have 72/22/8 cells. All statements below are measured outputs or explicitly analytic calculations. All conditions, including unfavorable and undefined results, remain in complete tables. The examples explain H1–H4; they are not multiplicity-adjusted discovery tests or universal estimator rankings.

Numeric brackets below are approximate 95% uncertainty intervals. Synthetic family values average graph summaries equally and use t4 intervals over five independent graph draws. They include finite Monte Carlo variation; they are not isolated pure graph-generation variance estimates. SNAP and the one-seed imbalance slice use conditional-on-graph Monte Carlo intervals (normal/delta moments or Wilson coverage), not graph-population intervals. Full definitions and finite/estimable denominators are in methods.md.

Every value selected by this script is registered with its exact source CSV SHA256, row selector, metric, scale, denominator and uncertainty in results/diagnostics/claim_evidence.csv. Operational risk retains finite minimum-norm fits even if their endpoint is nonestimable; partially defined methods have conditional-defined risk plus a failure rate. Oracle covariance/mean quantities are simulation-only diagnostics.

## H1: degree, size and the conditional bias/variance diagnostic

Linear DGP, matched linear model, node assignment, p=.5/rho0; all endpoint contrasts are estimable:

|n|degree|Mean graph RMSE [graph CI]|Mean oracle variance [graph CI]|
|--:|--:|--:|--:|
|2000|4|0.10086 [0.098875, 0.10285]|0.010046 [0.010022, 0.010069]|
|2000|20|0.20715 [0.20071, 0.2136]|0.04257 [0.042446, 0.042693]|
|2000|80|0.41209 [0.39463, 0.42954]|0.16914 [0.16879, 0.16949]|
|8000|20|0.10077 [0.09779, 0.10375]|0.010534 [0.010521, 0.010547]|

At fixed n, error grows with degree; at fixed degree it decreases with n in these regular-graph slices. Matched-model conditional mean bias is at numerical roundoff when the contrast is estimable (full audit max below 4e-13). This does not make variance a sufficient diagnostic for a misspecified mean, or infer general rates across all graph laws. E[b(z)^2], rather than E[b(z)]^2, belongs in the MSE decomposition. Exact b²+v is checked by executable small-graph identities and retained in every regression output; simulation residual means have MCSE, not an asserted finite-sample exact zero.

## H2: prediction is not global endpoint validation

Regular n2000/d20, cubic DGP, cluster assignment: cubic-minus-linear GATE MSE 0.13242 [0.1054, 0.15943]; fresh-assignment noisy-outcome prediction MSE -0.0019797 [-0.0022731, -0.0016863]. Both fits are fully defined and estimable. Within-cell differences preserve shared assignments/noise. The better interior prediction model has worse GATE here.

Linear regression on the quadratic DGP, regular n2000/d20/node/p=.5: signed bias -0.002102 [-0.023381, 0.019177]. This is consistent with the analytic complement cancellation of signed bias at .5, not proof of small assignment-conditional bias or general robustness. The focused independent imbalance panel breaks that symmetry:

|fixed graph|design|p|Signed bias [conditional MC CI]|
|--|--|--:|--:|
|regular|bernoulli|0.2|-0.57553 [-0.60164, -0.54942]|
|regular|bernoulli|0.8|0.5549 [0.53089, 0.57891]|
|regular|cluster|0.2|-0.43189 [-0.45433, -0.40946]|
|regular|cluster|0.8|0.4411 [0.41857, 0.46364]|
|facebook|bernoulli|0.2|-0.40288 [-0.41976, -0.38599]|
|facebook|bernoulli|0.8|0.41416 [0.39589, 0.43243]|
|facebook|cluster|0.2|-0.28673 [-0.29713, -0.27634]|
|facebook|cluster|0.8|0.28169 [0.27172, 0.29166]|

The regular imbalance graph is n2000/d20, seed201 only; SNAP is its one fixed topology. Signs reverse under both designs on these two graphs. These are not five-graph imbalance population results.

## H2: hidden-tail nonidentification control

Regular n2000/d20, node assignment: observed identical-data event probability 0.1005 [0.074584, 0.12642]; coupled linear-DGP MSE 0.042934 [0.040265, 0.045602] and hidden-tail MSE 1.0464 [1.0027, 1.0901]. The target gap is one; the estimator returns the same value on identical data.
Regular n2000/d80, node assignment: observed identical-data event probability 1 [1, 1]; coupled linear-DGP MSE 0.16997 [0.15554, 0.18441] and hidden-tail MSE 1.1368 [1.0846, 1.1891]. The target gap is one; the estimator returns the same value on identical data.
Analytic regular d20 union bound: P(identical data)>=0.5975494385, so the maximum of the two unconditional MSEs is at least 0.1493873596. This is computed by gatebench.support_bounds, not estimated from the R400 events.
Analytic regular d80 union bound: P(identical data)>=0.9999999795, so the maximum of the two unconditional MSEs is at least 0.2499999949. This is computed by gatebench.support_bounds, not estimated from the R400 events.

The analytic statement concerns a shared, fully defined estimation rule. It cannot be applied to the conditional-success risk of a partially defined Hajek estimator. The same sparse-interior observations can have distinct endpoint truths; no choice among the implemented smoothers certifies robustness to this tail without additional response assumptions.

## H3: design can help support without guaranteeing lower risk

Regular d4, matched linear DGP/model: cluster-minus-node RMSE -0.033054 [-0.035343, -0.030766]. This is an independent-stream contrast, then averaged over matched graphs; it is not replicate-paired.
Regular d20, matched linear DGP/model: cluster-minus-node RMSE -0.041554 [-0.053898, -0.02921]. This is an independent-stream contrast, then averaged over matched graphs; it is not replicate-paired.
Regular d80, matched linear DGP/model: cluster-minus-node RMSE -0.049637 [-0.078725, -0.020548]. This is an independent-stream contrast, then averaged over matched graphs; it is not replicate-paired.
Dense threshold oracle, bernoulli: operational RMSE 1.0001 [0.99674, 1.0035]; estimable fraction 0.002 [-0.00059713, 0.0045971].
Dense threshold oracle, cluster: operational RMSE 0.80502 [0.78721, 0.82282]; estimable fraction 0.635 [0.61625, 0.65375].
Dense linear DGP/fixed spline, bernoulli: operational RMSE 820.37 [-393.54, 2034.3]; estimable fraction 0 [0, 0].
Dense linear DGP/fixed spline, cluster: operational RMSE 3946.3 [3199.6, 4692.9]; estimable fraction 0.269 [0.23934, 0.29866].

Cluster assignment improves matched low-dimensional regression here, but fixed-spline risk can become much larger while estimability improves. The dense threshold example also fails often despite being given the correct response feature. Unsupported finite fits remain operational errors, never successful endpoint recovery. Wide untruncated graph t intervals may extend below zero for unstable nonnegative metrics; the negative limit signals imprecision, not negative risk. Fixed BFS partitions, their cluster counts/retained edges and exposure summaries are reported; this is not a cluster-optimization study. ER/SBM/BA contrasts change several structural properties and are descriptive, not isolated causal topology effects.

## H4: correct mapping can trade bias for variance

|n|degree|twohop-minus-linear GATE MSE [graph CI], twohop DGP/node|
|--:|--:|--:|
|2000|4|-0.11649 [-0.12133, -0.11165]|
|2000|20|0.55484 [0.47631, 0.63337]|
|8000|20|-0.03851 [-0.051083, -0.025937]|

The correctly mapped fit removes conditional mean bias when estimable, but its larger endpoint variance can dominate at n2000/d20. The adverse case and the reversal at n8000 are both retained; there is no universal correct-map risk lower bound. The twohop mechanism includes random-walk return paths, not solely distinct-distance-two neighbors.

## H4: local covariance, uncertainty and conditional public-graph evidence

rho1 regular/bernoulli, matched linear fit: RMSE 0.22839 [0.22009, 0.23668]; HC3 coverage 0.9205 [0.91495, 0.92605]; oracle coverage 0.9475 [0.93528, 0.95972].
Independent rho1-minus-rho0 RMSE 0.021234 [0.016296, 0.026173].
rho1 regular/cluster, matched linear fit: RMSE 0.18993 [0.18381, 0.19606]; HC3 coverage 0.919 [0.90726, 0.93074]; oracle coverage 0.947 [0.93376, 0.96024].
Independent rho1-minus-rho0 RMSE 0.024335 [0.012128, 0.036542].
rho1 sbm/bernoulli, matched linear fit: RMSE 0.227 [0.21725, 0.23675]; HC3 coverage 0.9105 [0.88884, 0.93216]; oracle coverage 0.9475 [0.93107, 0.96393].
Independent rho1-minus-rho0 RMSE 0.028008 [0.016068, 0.039948].
rho1 sbm/cluster, matched linear fit: RMSE 0.18693 [0.18004, 0.19381]; HC3 coverage 0.8395 [0.8223, 0.8567]; oracle coverage 0.9555 [0.94747, 0.96353].
Independent rho1-minus-rho0 RMSE 0.053032 [0.044169, 0.061895].

|SNAP design/rho|RMSE [MC CI]|HC3 coverage [Wilson CI]|oracle coverage [Wilson CI]|Mean HC3 interval width|Mean oracle interval width|
|--|--:|--:|--:|--:|--:|
|bernoulli/0|0.11136 [0.10355, 0.11918]|0.94 [0.91228, 0.95935]|0.9425 [0.9152, 0.96138]|0.43168|0.43123|
|bernoulli/1|0.2579 [0.24006, 0.27575]|0.5875 [0.53865, 0.63469]|0.94 [0.91228, 0.95935]|0.42743|0.9652|
|cluster/0|0.054443 [0.051047, 0.05784]|0.9675 [0.9452, 0.98091]|0.9675 [0.9452, 0.98091]|0.22418|0.22385|
|cluster/1|0.13334 [0.12424, 0.14244]|0.59 [0.54117, 0.63712]|0.9375 [0.90937, 0.95731]|0.22281|0.47653|

All displayed matched-model coverage denominators are 400 per graph. The local row-normalized rho1 law has unit marginal variances and this particular network covariance. HC3 is working independence; the oracle uses the true covariance and conditional unbiasedness. Near-nominal oracle coverage does not provide a feasible network inference method or protect a misspecified mean. Positive rho does not establish the sign/magnitude of variance change for every possible contrast or noise law. All public-graph uncertainty is conditional on one historical topology, its fixed x and partition.

## Baselines and negative controls

Sparse regular/node/no_interference/naive: mean graph RMSE 0.049783 [0.04865, 0.050917]; defined fraction 1 [1, 1].
Sparse regular/node/no_interference/linear: mean graph RMSE 0.10086 [0.098875, 0.10285]; defined fraction 1 [1, 1].
Sparse regular/node/no_interference/ht: mean graph RMSE 0.26128 [0.24599, 0.27656]; defined fraction 1 [1, 1].
Sparse regular/node/no_interference/hajek: mean graph RMSE 0.20083 [0.18997, 0.21169]; defined fraction 1 [1, 1].
Sparse regular/node/linear/naive: mean graph RMSE 1.0036 [1.0003, 1.0068]; defined fraction 1 [1, 1].
Sparse regular/node/linear/linear: mean graph RMSE 0.10086 [0.098875, 0.10285]; defined fraction 1 [1, 1].
Sparse regular/node/linear/ht: mean graph RMSE 0.39179 [0.37057, 0.41301]; defined fraction 1 [1, 1].
Sparse regular/node/linear/hajek: mean graph RMSE 0.20083 [0.18997, 0.21169]; defined fraction 1 [1, 1].

Without interference, unnecessary exposure adjustment costs precision relative to DIM in this sparse control. With linear interference, DIM has substantial missing-spillover bias and matched regression improves accuracy. These examples do not assert that regression dominates all baselines under arbitrary outcome laws.

Regular n2000/d20/node/linear DGP Hajek defined fraction 0 [0, 0]. Its conditional-defined RMSE is missing when no return exists. Undefined estimates are not zero error. Full-exposure HT remains mathematically unbiased only for its one-hop mapping; in the twohop DGP it is a misspecified comparator.
SNAP/rho0/bernoulli one-hop HT exact log10(RMSE) 154.26. The R400 empirical risk and normal intervals can miss astronomically rare contributions. All306 exact endpoint-family rows remain in exact_ht_risk.csv; endpoint families reuse identical one-hop means/covariance, not the twohop identification.
SNAP/rho0/cluster one-hop HT exact log10(RMSE) 12.923. The R400 empirical risk and normal intervals can miss astronomically rare contributions. All306 exact endpoint-family rows remain in exact_ht_risk.csv; endpoint families reuse identical one-hop means/covariance, not the twohop identification.

The exact risks are fixed-graph, fixed-covariate, known-DGP calculations, not population guarantees. No practical interval is implemented for HT/Hajek; nonempty-arm DIM has stored HC3/oracle intervals from its own-treatment regression.

## Complete failure ledger and reproducibility scope

|model|estimator_output_rows|undefined_count|unsupported_defined_count|undefined_count_distinct_assignment_cells|unsupported_defined_count_distinct_assignment_cells|
|--|--|--|--|--|--|
|cubic|326400|0|0|0|0|
|hajek|326400|159080|0|19885|0|
|ht|326400|0|0|0|0|
|linear|326400|0|0|0|0|
|naive|326400|0|0|0|0|
|quadratic|326400|0|0|0|0|
|spline|326400|0|34704|0|4338|
|threshold_oracle|326400|0|25104|0|3138|
|twohop|326400|0|0|0|0|

Each estimator has 326400 output rows = 40800 graph/design/p/noise repetitions × 8 mechanisms. The failure inventory counts outputs for accounting and gives distinct assignment-cell events separately; repeated mechanisms are not independent failure observations. No DIM empty arm or nonfinite HT output occurred; the explicit failure policies are still implemented. Finite nonestimable spline/threshold outputs are counted separately from undefined Hajek. The 102-cell ledger has no unrun or failed cell. Selected replay exactly matched 115200 rows in four predeclared structural cells; this is not a full-study replay or independent implementation.

No excluded scope was relabeled as a negative result: no second public graph, missing-edge/treatment-strength/cluster-size grid, adaptive feature selection or GNN was run. Five synthetic graph draws, one public topology, gamma1, fixed response/noise laws, and normal/delta finite-run risk intervals limit generalization and tail precision. All fitted bases/tuning are fixed; no estimator/grid was selected by its production accuracy.

## Required evidence routes

|Question / requirement|Actual evidence|
|--|--|
|H1 degree/size and b²+v|summary/performance_by_{graph,family}.csv; diagnostics/diagnostics_by_{graph,family}.csv; code/tests/test_identities.py|
|H2 misspecification, prediction, allocation, tail coupling|summary/paired_by_*.csv; diagnostics/prediction_gate_pairs_by_*.csv, support_coupling_by_*.csv; production_imbalance/; support_bounds.json|
|H3 assignment/topology/support/failure|diagnostics/independent_contrasts_by_*.csv, graph_inventory.csv, failure_inventory.csv; complete performance/validity tables|
|H4 mapping/noise/coverage/rare risk|paired_by_*.csv; independent_contrasts_by_*.csv; diagnostics_by_*.csv; exact_ht_risk.csv and all102 exact_ht JSON checkpoints|
|Completeness/provenance|analysis/production_audit.json, summary_audit.json, execution_manifest.json, final_execution.json, cell_ledger.csv; raw metadata/Parquet; summary and diagnostics manifests|
|Clean replay / environment / commands|analysis/reproduction_audit.json, postprocessing_timings.json, delivery_reproduction.md; code/environment.json, requirements-lock.txt; download_data.py, run_study.py, finalize_results.py, final_report.py|

This handoff is the analysis owner’s evidence and validity record. Presentation owns final figures/tables, paper owns report integration, story owns protocol coverage, and internal review retains independent release judgement.
