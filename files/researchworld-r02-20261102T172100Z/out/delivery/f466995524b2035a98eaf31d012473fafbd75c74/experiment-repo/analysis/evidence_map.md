# Analysis evidence map (generated from measured results)

All brackets below are pointwise 95% independent-replication t intervals. No pilot values enter this map. Main results have 100 independent train/calibration/test replications per cell, 5000 test observations per environment. The selected examples below illustrate prespecified comparisons; every cell remains in the supplied tables. A pointwise CI is neither an equivalence test nor a simultaneous certificate.

## Files and exact display keys

`results/main_summary/summary.csv`: k, ncal, scenario, shift, epsilon, alpha, method, metric, n_rep, n_rep_total, summary_status, mean, se, ci_low, ci_high. Main alpha=.1 and epsilon=1e-6 (no zeros, so epsilon has no effect). `paired_contrasts.csv`: same condition keys plus method_a/method_b, metric, mean_difference and paired CI. `shift_contrasts.csv`: shift-minus-iid mean/CI within method and seed. `replications.csv`: every data estimate and subgroup/calibration count. `diagnostics.csv`: coverage SD/quantiles, empirical below-.85 fraction with Wilson CI, infinite/null counts. `area_precision.csv`: common-candidate MC upper bound and ordering resolution. Raw files are `results/main.jsonl` and `results/weighted.jsonl`, with source hashes/arguments and per-cell timings. See `results/audit.json` for structural audit, actual resource cost, counts and exclusions.

## RQ1: simultaneous reliability requires simultaneous calibration

At K=3, ncal=499, heterogeneous iid: coordinate-naive joint coverage is 0.8390 [0.8357, 0.8424]; Bonferroni is 0.9360 [0.9339, 0.9380]; raw L2 is 0.9016 [0.8987, 0.9044]; global Aitchison is 0.9017 [0.8988, 0.9045]. At K=10 the naive result is 0.6380 [0.6328, 0.6432]. These are observed-composition simultaneous coverages, not class-label coverage. Full iid marginal means for joint methods remain near their rank target across the matrix; do not describe all pointwise intervals as containing .9 or all methods as equally efficient.

## RQ2: good marginal coverage hides observed-group misses

At the same K=3/ncal499 heterogeneous iid cell, global Aitchison group1 coverage is 0.5069 [0.4931, 0.5207], while Mondrian is 0.9063 [0.9010, 0.9116] and learned scaling is 0.8988 [0.8935, 0.9041]. Report group0 too, from the same rows. This is a predeclared observed group with high noise; no claim about arbitrary latent subgroups follows.

Important negative finding: at K=10/ncal499, learned-scale group1 iid coverage is 0.8940 [0.8893, 0.8988], below the nominal target in this pointwise estimate. Group1 under shift is 0.8947 [0.8901, 0.8993]. Scaling helps this generator strongly but does not deliver a group guarantee.

## RQ3: efficiency depends on geometry and evaluation environment

For K=3/ncal499 heterogeneous iid, area fractions are global Aitchison 0.2525 [0.2429, 0.2621], scaled 0.1574 [0.1495, 0.1654], Mondrian 0.1636 [0.1552, 0.1721], raw L2 0.2316 [0.2218, 0.2414], raw max 0.2303 [0.2206, 0.2400]. Paired scaled-minus-global area: -0.0951 [-0.1080, -0.0821]; Mondrian-minus-global: -0.0889 [-0.1023, -0.0755]. The metric is a chosen Euclidean-simplex reference. Display coverage beside area. These results are not a universal ranking, nor evidence of group-valid raw/global efficiency.

Under the shifted environment, the Mondrian area is 0.4809 [0.4679, 0.4938] and oracle weighted area is 0.5632 [0.5514, 0.5749]; weighted-minus-Mondrian paired difference is 0.0823 [0.0724, 0.0921]. The global region is much smaller but severely undercovers there, so do not call it a reliable efficiency winner. No K=10 cross-geometry area ranking is supplied.

`area_precision.csv` uses a conservative upper bound on candidate-only MC SE of each paired mean. Candidate uncertainty is smaller than the relevant claimed differences. Withhold every ordering whose paired CI includes zero (including the source-driven TV/raw-L2 comparisons); examples from the original core are: raw L2/max versus clr under heterogeneous shift at ncal99, and scaled versus clr under homogeneous shift at both ncal. Weighted and ordinary clr under iid are exactly the same algorithm/stream, not a noisy unresolved contrast. There are no zero total-area estimates in the main records. Candidate-only MC SE max across records is in audit.json; it is distinct from anchor/calibration variability.

## RQ4: specified mixture shift and oracle information

At K=3/ncal499 heterogeneous shift, global clr marginal coverage is 0.6050 [0.5944, 0.6157], Mondrian 0.9055 [0.9013, 0.9097], oracle weighted 0.9066 [0.9019, 0.9113], and learned scale 0.8976 [0.8934, 0.9017]. Weighted group1 coverage is 0.8831 [0.8772, 0.8889], demonstrating that target-marginal validity and group validity differ even for the oracle known-ratio remedy. Use paired `shift_contrasts.csv` for iid-to-shift estimates, rather than treating the two means as independent. Shift changes only observed-group mixture weights; these results do not evaluate arbitrary shift or estimated density ratios.

## Realized-calibration variability

Use `diagnostics.csv` or `replications.csv` for ECDF/10th quantile and below-.85 displays at both calibration sizes. Wilson intervals apply to the frequency of finite-test estimates below the prespecified tolerance, not to exact population-conditional coverage. Zero observed failures still have a nonzero Wilson upper bound. All 160 main method/environment/cell combinations have 100 replications, including oracle weights. No main infinite threshold was realized; rank/tiny-group checks explicitly cover that behavior.

## Exact zeros and replacement are different response targets

At K=10/ncal499 and epsilon=1e-8, transformed-target clr coverage is 0.8990 [0.8954, 0.9026]; the same region tested on original responses under the stated positive-domain rule covers 0.4721 [0.4702, 0.4740]. Original-target raw L2 covers 0.9000 [0.8955, 0.9045]. The boundary rate and its CI are in `results/boundary_summary/zero_prevalence.csv`. Do not label the direct untransformed clr ball zero-safe. The explicitly defined pullback region {y:T_epsilon(y) in C_epsilon(x)} has exactly the measured transformed membership event and therefore the same coverage and CI for original Y. It is a different region; its original-simplex area was not estimated. `pullback_equivalence.csv` gives these values as an exact identity from the measured transformed rows, not a new simulation.

All 50-rep K3/K10 epsilon cells (1e-8,1e-4,1e-2) are in `boundary_summary/summary.csv`; paired changes relative to 1e-8 are in `epsilon_contrasts.csv`. The original datasets are identical across epsilon. Epsilon changes fitted centers/scales and the response target, even where marginal coverage remains near .9; the naive-coordinate control can be very sensitive. Structural-zero mechanisms and realistic applications are not established by this censoring stress test.

## Numerical validation, provenance and failures

`results/rank_checks.csv` contains 30 predeclared ncal/alpha/law cells, 20000 independent trials each; exact continuous Beta rank mean/variance and discrete tie expectations accompany observations. `analysis/checks.py` additionally checks analytic area, perturbation/ilr invariance, nesting, empty/tiny groups, weighted test atoms and mixed finite/infinite summaries. All actually passed. `analysis/methods.md` provides exact generator, fitted basis, training-scale algorithm, weighted quantile, scope and primary-source verification. `analysis/notes/*freeze.md` preserves the pre-run matrix and sensitivity decisions. No resource run failed and no main/extension/boundary replication was excluded; only the declared pilot is excluded from final evidence. A caught serialization defect was corrected before main execution and is documented in notes/checks. Core resource CPU was 124.165104 s; extensions 45.080784 s. The resource reported running times of116.110 s for core and43.878 s for initial extensions; the source-driven score supplement reports44.498 s/45.631351 CPU s, while its per-cell timing sum is stored separately. Startup and summary time are additional. The actual manifests/timing logs permit checking those figures.

## Handoff boundaries

The analysis supports a bounded synthetic evaluation with known group/shift structure. It does not support an exhaustive method survey, a novel universal theorem, real-data utility, unknown-group adaptation, arbitrary shift, or a geometry-independent best method. The presentation owner owns all final figures/tables and their generators; the report owner owns manuscript prose and claims. This file is the source-to-claim interface for those owners.

## Source-driven TV and forward-KL controls

Both added scores have 100 fresh matched datasets per cell in results/prior_scores.jsonl and are included in all main summary/paired/shift tables. At K3/ncal499 heterogeneous iid, TV coverage is 0.9017 [0.8988, 0.9045], forward KL coverage is 0.9022 [0.8997, 0.9048], and forward-KL high-noise group coverage is 0.5110 [0.4988, 0.5231]. Under shift, forward-KL marginal coverage is 0.6083 [0.5985, 0.6181]. Their ordinary joint calibration does not repair subgroup or unweighted-shift failures.

At the same iid cell, forward-KL area is 0.2158 [0.2075, 0.2240]; paired KL-minus-raw-L2 area is -0.0158 [-0.0197, -0.0120], and KL-minus-clr is -0.0367 [-0.0423, -0.0312]. Compare only with coverage visible and the chosen uniform-simplex reference stated. Do not assert a universal best geometry. K3 TV is exactly raw max: all800 matched coverage/group/area records agree bit for bit. TV is distinct at K10. These controls were required from permitted prior work after core results were inspected by analysis, before their own outcomes were known. They compare scores under a shared model, not the prior study's full fitted pipeline. See the separate supplement freeze, source manifest/timings and audit fields.
