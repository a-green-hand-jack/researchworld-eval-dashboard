# Corrected completed core evidence memo

Scope:72/72core cells,400repetitions/cell, all five synthetic graph seeds and the full SNAP graph. Noise and imbalance panels are outside this memo. Synthetic-family values below are equal-graph means with approximate95% t4 intervals; public-graph values have conditional Monte Carlo intervals. These are selected explanatory comparisons from complete tables, not multiplicity-adjusted discoveries or universal risk rankings. The complete raw/family/paired tables retain every planned core condition.

## H1: conditional contrast variance and degree/size

Linear DGP, correctly specified linear regression, node Bernoulli(.5): all fits are endpoint-estimable.

|n|degree|Mean graph RMSE [95% graph CI]|sqrt(mean oracle variance)|
|--:|--:|--:|--:|
|2000|4|0.1009 [0.09888, 0.1029]|0.1002|
|2000|20|0.2072 [0.2007, 0.2136]|0.2063|
|2000|80|0.4121 [0.3946, 0.4295]|0.4113|
|8000|20|0.1008 [0.09779, 0.1037]|0.1026|

Degree increases error at fixed n; increasing n at fixed degree reduces it. The oracle variance is explanatory simulation evidence, not a feasible certificate under misspecification. The first column averages RMSE across graphs; the last takes the square root after averaging variance.

## H2: prediction and endpoint accuracy can disagree

Cubic-minus-linear regression on the cubic DGP, regular n2000/d20 under cluster assignment: GATE MSE difference 0.1324 [0.1054, 0.1594]; fresh-assignment noisy-outcome prediction MSE difference -0.00198 [-0.002273, -0.001686]. Both contrasts use the same within-cell streams; positive means cubic is worse. Both methods are fully defined/estimable here. Improved interior prediction therefore does not certify improved GATE.

Linear regression on quadratic: signed bias -0.002102 [-0.02338, 0.01918], mean RMSE 0.2086 [0.2028, 0.2144].
Linear regression on cubic: signed bias -0.2157 [-0.2369, -0.1945], mean RMSE 0.3009 [0.284, 0.3178].
The near-zero signed quadratic bias agrees with complement cancellation; it does not imply that quadratic conditional biases or all forms of misspecification vanish. The imbalance check remains separate.

## H3/H4: correct mapping and cluster support have conditional value

Twohop DGP, twohop-minus-linear regression under node assignment:

|n|degree|GATE MSE difference [95% graph CI]|linear mean RMSE|twohop mean RMSE|
|--:|--:|--:|--:|--:|
|2000|4|-0.1165 [-0.1213, -0.1117]|0.3884|0.1854|
|2000|20|0.5548 [0.4763, 0.6334]|0.5209|0.9086|
|8000|20|-0.03851 [-0.05108, -0.02594]|0.4828|0.4412|

The shape/mapping-aware model removes conditional mean bias when estimable, but it is not a risk lower bound: its larger endpoint noise variance can outweigh that repair. Keep the adverse degree20 n2000 result alongside the favorable sparse result and the larger-n comparison.

|Threshold DGP, shape-aware oracle|Mean graph RMSE [95% graph CI]|Estimable fraction|
|--|--:|--:|
|degree4, bernoulli|0.06594 [0.06429, 0.06758]|1|
|degree80, bernoulli|0.9994 [0.9958, 1.003]|0.006|
|degree80, cluster|0.7488 [0.7319, 0.7656]|0.7205|

Correct response features can fail at unsupported endpoints. The operational RMSE above includes every finite minimum-norm estimate; estimable-only risk is a separate conditional metric. Cluster assignment raises threshold estimability in the dense case but does not make every fit identified.

Dense linear DGP, fixed spline under bernoulli: mean graph RMSE 820.4 [-393.5, 2034], estimable fraction 0.
Dense linear DGP, fixed spline under cluster: mean graph RMSE 3946 [3200, 4693], estimable fraction 0.269.
This is an adverse flexible-fit example: greater support/estimability under clusters does not guarantee lower operational error. Very large, unstable spline risks and wide five-graph intervals must remain visible; unsupported minimum-norm returns are not endpoint recovery. Untruncated symmetric t intervals can extend below zero for unstable nonnegative metrics; that reflects poor precision and does not imply negative true risk.

## Fixed public topology and rare-exposure tails

Full SNAP, linear DGP/linear regression, bernoulli: RMSE 0.1114 [0.1035, 0.1192] (conditional MC95%), HC3 coverage 0.94 [0.9123, 0.9594], oracle coverage 0.9425 [0.9152, 0.9614].
Full SNAP, linear DGP/linear regression, cluster: RMSE 0.05444 [0.05105, 0.05784] (conditional MC95%), HC3 coverage 0.9675 [0.9452, 0.9809], oracle coverage 0.9675 [0.9452, 0.9809].
SNAP one-hop HT, bernoulli: empirical R400 RMSE 4.837; exact log10(RMSE) 154.257. The empirical number and its normal interval miss rare-event risk and cannot be used as the true-risk comparison.
SNAP one-hop HT, cluster: empirical R400 RMSE 4.023; exact log10(RMSE) 12.9229. The empirical number and its normal interval miss rare-event risk and cannot be used as the true-risk comparison.

The historical public graph has synthetic outcomes and fixed covariates/partition; it is a conditional topology case, not real-platform effect validation. Exact HT risk is one-hop/oracle evidence; twohop has an intentionally misspecified one-hop comparator and is excluded from that identity.

## Provenance and limits

Generated by code/scripts/core_report.py (scripts/core_report.py in the analysis repository) from results/core_summary/{performance_by_graph,performance_by_family,paired_by_family}.csv and production_core/exact_ht/*.json. Standard summary_manifest.json hashes all72raw inputs and its source. The complete corrected checkpoint and exact-input audit receipts are production_audit.json and summary_audit.json. The full102-cell summary audit includes every core row; v1 core-only receipts are archived under roundoff_v1/. The final complete-study claim map supersedes this stage memo; no noise/imbalance finding, complete 102-cell assertion, universal best estimator, novel estimator/theorem or practical oracle inference claim is made here.
