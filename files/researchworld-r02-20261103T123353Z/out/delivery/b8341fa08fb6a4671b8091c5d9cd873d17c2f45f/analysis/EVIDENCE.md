# Executed analysis evidence and limits

All results below come from the frozen observed-composition study. This is the analysis owner’s numerical handoff; the report and final figures are delivered by their owners.

## Inventory and audit

All 1,900 trials in 19 frozen cells completed: 100 independent regenerated/refitted trials per cell, with 2,000 test observations each. Canonical exports have 44,600 method/group rows (42,600 defined procedure rows, 2,000 explicit unsmoothed-ILR inapplicability rows). Pilots are excluded. Scientific generation/audit source pin is `4d760d511a3105b6d5b33937ff07124e630a64c5`. Complete seed/input/fit and checkpoint hashes are retained in results/confirmatory/.

The prescribed audit covers 3,008 matched method/center regions and 3,616 paired numerical contrasts: every K3 cell, repeats 0/25/50/75, first four centers per observed X group, four independent power16 scrambles. Recalculation of every allowance differs by at most 9.97e-17. Maximum measured allowance is 0.004229, not the .001 floor. Of 339 reported cell/group method-area contrasts, 76 remain numerically/statistically unresolved and 258 pass the frozen geometric resolution and practical-effect rule. These flags alone never make an under-covering control preferable.

`final_audit.json` verifies full trial inventory, no duplicate rows, all source/config hashes against the frozen git object, identical source across shards, the exact complete method/center audit key set, matching main areas, every raw scramble summary, paired allowance recomputation/interval enlargement and the 32 measured case memberships. It is a reproducibility/consistency audit, not independent report approval.

## Reliability and the coordinate control

| Cell | Naive coordinate joint coverage | Bonferroni joint coverage | Operative ILR joint coverage |
| --- | --- | --- | --- |
| interior_k3 | 0.780620 [0.776577, 0.784663] | 0.921495 [0.918807, 0.924183] | 0.898655 [0.895555, 0.901755] |
| interior_k10 | 0.321485 [0.317591, 0.325379] | 0.898125 [0.894991, 0.901259] | 0.899080 [0.895892, 0.902268] |
| boundary_k3 | 0.818030 [0.814579, 0.821481] | 0.936275 [0.934021, 0.938529] | 0.898985 [0.895956, 0.902014] |
| boundary_k10 | 0.465620 [0.461973, 0.469267] | 0.912090 [0.909262, 0.914918] | 0.899490 [0.897064, 0.901916] |
| dirichlet_k3 | 0.795825 [0.791964, 0.799686] | 0.927775 [0.925312, 0.930238] | 0.900455 [0.897815, 0.903095] |
| dirichlet_k10 | 0.341790 [0.337581, 0.345999] | 0.907585 [0.904492, 0.910678] | 0.900360 [0.897608, 0.903112] |
| zeros_k3 | 0.784330 [0.780486, 0.788174] | 0.925585 [0.923251, 0.927919] | 0.899485 [0.896805, 0.902165] |
| zeros_k10 | 0.266905 [0.263409, 0.270401] | 0.898995 [0.895981, 0.902009] | 0.899450 [0.896448, 0.902452] |

The naive coordinate method calibrates each coordinate separately and fails the desired joint event in these cells. Componentwise coverage is in summary/component_coverage_summary.csv; paired component-minus-joint gaps are in derived/coordinate_component_joint_gaps.csv. Bonferroni controls the joint event under the stated assumptions. These tables test the directly observed composition, not a class label or an unobserved probability vector.

## Marginal reliability can conceal minority failure

| Cell | Procedure | Population coverage | Minority coverage | Paired minority improvement over global ILR |
| --- | --- | --- | --- | --- |
| heterogeneous_k3 | ilr | 0.900800 [0.898046, 0.903554] | 0.160954 [0.153352, 0.168555] | reference |
| heterogeneous_k3 | ilr_scaled | 0.897285 [0.894353, 0.900217] | 0.892055 [0.884172, 0.899937] | 0.731101 [0.720911, 0.741291] |
| heterogeneous_k3 | ilr_mondrian | 0.899120 [0.896139, 0.902101] | 0.904446 [0.895541, 0.913350] | 0.743492 [0.731706, 0.755279] |
| heterogeneous_k10 | ilr | 0.900250 [0.897479, 0.903021] | 0.051147 [0.037090, 0.065205] | reference |
| heterogeneous_k10 | ilr_scaled | 0.898230 [0.895437, 0.901023] | 0.888456 [0.880813, 0.896100] | 0.837309 [0.823079, 0.851539] |
| heterogeneous_k10 | ilr_mondrian | 0.900290 [0.897576, 0.903004] | 0.909591 [0.900819, 0.918363] | 0.858444 [0.842926, 0.873961] |

Global marginal calibration leaves severe high-variance-minority undercoverage. Both fitted scale adaptation and fixed-group calibration improve it, but fitted scaling does not grant group validity and the measured minority mean is below .9 in the core cells. The group theorem averages over within-group calibration values and future observations, not each realized split or every covariate value. Group sizes/fitted scales are in derived/group_denominators_and_fits.csv.

## Conditional geometry ordering and unresolved comparisons

Area is normalized original-simplex Hausdorff area. Each interval below is the paired statistical t95 interval enlarged by the separately measured empirical numerical allowance. A negative value means the first procedure’s region is smaller at the recorded coverage, not universally preferable.

| Cell | Area contrast | Mean and enlarged interval |
| --- | --- | --- |
| interior_k3 | ILR minus L2 | -0.043940 [-0.047637, -0.040243] (allowance 0.001000; resolved at practical margin) |
| heterogeneous_k3 | ILR minus L2 | -0.024893 [-0.029121, -0.020665] (allowance 0.001000; resolved at practical margin) |
| boundary_k3 | ILR minus L2 | 0.049773 [0.045541, 0.054006] (allowance 0.001000; resolved at practical margin) |
| dirichlet_k3 | ILR minus L2 | 0.177054 [0.170228, 0.183880] (allowance 0.001000; resolved at practical margin) |
| interior_k3 | TV minus L2 | 0.000736 [-0.001499, 0.002971] (allowance 0.001000; no practical ranking) |
| boundary_k3 | TV minus L2 | -0.000895 [-0.002336, 0.000545] (allowance 0.001000; no practical ranking) |
| dirichlet_k3 | TV minus L2 | -0.000167 [-0.001634, 0.001300] (allowance 0.001000; no practical ranking) |
| zeros_k3 | TV minus L2 | 0.002868 [-0.002127, 0.007863] (allowance 0.003044; no practical ranking) |
| zeros_k3 | ILR-smoothed minus L2 | 0.239934 [0.230442, 0.249426] (allowance 0.002915; resolved at practical margin) |
| heterogeneous_k3 | scaled ILR minus global ILR | 0.012217 [0.006082, 0.018352] (allowance 0.001000; resolved at practical margin) |
| heterogeneous_k3 | group ILR minus global ILR | 0.013843 [0.007667, 0.020020] (allowance 0.001000; resolved at practical margin) |

The ILR-versus-L2 area ordering reverses between interior and boundary/Dirichlet mechanisms. TV versus L2 has no practically resolved ordering in any core K3 mechanism under the frozen rule. ILR versus Hellinger in the interior/heterogeneous mechanisms also remains unresolved. Minority reliability improves with adaptation/group calibration at a measured population-area cost; the small scaled-versus-group area contrast remains unresolved. Any smaller naive-coordinate region is accompanied by joint undercoverage and cannot be presented as better calibrated efficiency. No K10 area was measured. All orderings are conditional on the shared inverse-ILR ridge center and these synthetic mechanisms.

## The specified group-prevalence shift

| Procedure | Shifted population coverage | Shifted minority coverage |
| --- | --- | --- |
| ilr | 0.653915 [0.649874, 0.657956] | 0.159237 [0.152492, 0.165982] |
| ilr_scaled | 0.897400 [0.893766, 0.901034] | 0.895676 [0.888240, 0.903112] |
| ilr_mondrian | 0.902015 [0.898162, 0.905868] | 0.906485 [0.897815, 0.915155] |

Only P(G=1) changes from .1 to .4; the complete within-group law stays fixed. The measured marginal failure of global ILR and retained group-calibration coverage support this specific mechanism and the stated group-mixture proof. They do not establish arbitrary covariate- or response-shift robustness. Paired stress-minus-iid effects are in derived/paired_sensitivity_contrasts.csv; shared random-number pairing does not imply identical shifted test arrays.

## Calibration size, nominal level and small-group costs

| Cell | Procedure | Overall coverage | Minority coverage | Minority infinite-threshold frequency |
| --- | --- | --- | --- | --- |
| heterogeneous_ncal99 | group ILR | 0.905525 [0.899896, 0.911154] | 0.949291 [0.936360, 0.962222] | 0.310000 [0.217769, 0.402231] |
| heterogeneous_k3 | group ILR | 0.899120 [0.896139, 0.902101] | 0.904446 [0.895541, 0.913350] | 0.000000 [0.000000, 0.000000] |
| heterogeneous_ncal1999 | group ILR | 0.897830 [0.895886, 0.899774] | 0.894285 [0.888225, 0.900345] | 0.000000 [0.000000, 0.000000] |
| heterogeneous_alpha05 | group ILR | 0.949660 [0.947590, 0.951730] | 0.955311 [0.949003, 0.961618] | 0.000000 [0.000000, 0.000000] |

At ncal99, the recorded infinite-threshold frequency corresponds to 31 of 100 minority calibration groups receiving the entire valid target domain, retaining finite-rank conservatism rather than discarding those trials. At ncal1999 the group-calibrated mean is slightly below nominal in this finite run, so do not claim every observed mean is at least .9. Calibration-size and alpha paired contrasts are all retained.

| Interior cell | ILR coverage | Across-trial SD |
| --- | --- | --- |
| interior_ncal99 | 0.893865 [0.887741, 0.899989] | 0.030863 |
| interior_k3 | 0.898655 [0.895555, 0.901755] | 0.015621 |
| interior_ncal1999 | 0.898970 [0.896858, 0.901082] | 0.010645 |
| interior_alpha05 | 0.949730 [0.947515, 0.951945] | 0.011163 |

More calibration data reduces the observed procedure-to-procedure variation here, with finite-test noise still included. Alpha .05 targets .95 rather than .90. These are outer-trial summaries, not pooled binomial intervals.

## Exact zeros, smoothing and the limitation of area

| Cell | Score | Population coverage | Zero-face coverage | Positive-response coverage | Mean original-simplex area |
| --- | --- | --- | --- | --- | --- |
| zeros_k3 | l2 | 0.901700 [0.898812, 0.904588] | 0.692592 [0.685426, 0.699758] | 0.971525 [0.969715, 0.973334] | 0.757191 [0.750496, 0.763887] |
| zeros_k3 | hellinger | 0.900730 [0.897963, 0.903497] | 0.611547 [0.601352, 0.621742] | 0.997315 [0.996917, 0.997712] | 0.890406 [0.885346, 0.895466] |
| zeros_k3 | ilr_smoothed | 0.899485 [0.896805, 0.902165] | 0.598466 [0.587756, 0.609177] | 1.000000 [1.000000, 1.000000] | 0.997125 [0.996953, 0.997297] |
| zeros_eps1e-06 | ilr_smoothed | 0.899450 [0.896715, 0.902185] | 0.598359 [0.587458, 0.609259] | 1.000000 [1.000000, 1.000000] | 1.000018 [0.999994, 1.000041] |
| zeros_eps0.01 | ilr_smoothed | 0.899920 [0.897180, 0.902660] | 0.600265 [0.589354, 0.611176] | 0.999987 [0.999968, 1.000005] | 0.968920 [0.967228, 0.970613] |

Unsmoothed ILR is explicitly inapplicable to the entire true-zero arm; no zero response is silently dropped. The smoothed score is evaluated on original candidates and both arguments use the same fixed transform. Response-defined zero/positive slices are descriptive audits, not test-observable groups with a conditional theorem. Full-dimensional area assigns zero measure to faces; nearly full area can coexist with substantial face noncoverage.

At epsilon1e-6 the estimates saturate at normalized area one. 159 cell/trial/method/group mean estimates slightly exceed one (largest 1.000373924); they are retained unclipped as numerical warnings. Do not interpret a value above one, a tiny difference at this saturation, or a QMC estimate near one as an exact full-domain certificate. Cross-cell epsilon-area contrasts are descriptive statistical estimates and have no cross-cell area-ranking flag from the within-cell numerical allowance. Exact full-domain/unknown bounds and infinity remain separately saved.

## Uncertainty, contradictions and numerical limits

All displayed brackets are pointwise Student-t 95% intervals over independently regenerated/refitted trials, except explicitly enlarged area intervals. Trial SD and percentile bootstrap intervals (5,000 draws, seed90210) are retained alongside. They are not simultaneous familywise intervals, conditional-on-calibration guarantees, equivalence tests or p-value-selected findings. Positive-group missing area propagates undefined; zero-count groups have zero aggregate weight.

Not every finite-run joint-score interval contains nominal. Small pointwise shortfalls occur, including interior K10 L2, interior ncal99 ILR and some ncal1999 heterogeneous procedures; every estimate remains supplied. These pointwise outcomes across many correlated descriptive comparisons do not establish failure of the finite-rank exchangeability theorem. Scale adaptation does not eliminate all measured group gaps. No universal method winner is supported.

Precision flags in derived/coverage_gaps_and_precision.csv mark minority mean halfwidth>.02 (including heterogeneous ncal99 global ILR/Hellinger and the Bonferroni control, plus heterogeneous alpha05 Hellinger). Wide intervals do not establish equivalence. Bootstrap/t sensitivity is in derived/bootstrap_interval_sensitivity.csv. Numerical allowances are finite representative diagnostics, not uniform or simultaneous numerical-error bounds; 76 area contrasts remain unresolved and must stay so.

## Cost, failures, provenance and reproduction

The two scientific jobs, including all prescribed audits, used 2401.187 resource CPU seconds total and a creation-to-end parallel wall window of 1263.427 seconds. Main-run elapsed times were 1077.780 and 1154.991 seconds; peak main-run RSS was 181500 KiB. This replaces the pilot-derived runtime forecast. Both jobs succeeded and no scientific trial failed. Resource-clock, main-timer and CPU definitions are kept distinct in results/scientific_resources.json and resource_jobs.json; postprocessing costs are separate.

Historical failures/changes remain in DECISIONS.md, REPRODUCE.md and results/run_failures.json: the pre-pilot Jacobian normalization correction, a failed preconfirmatory launcher with a missing sandbox /tmp file (zero scientific trials affected), and a historical exploratory-pilot postprocessing check lacking input provenance. They are not measured negative scientific findings. No extra refits/trials were run to obtain final significance or reverse a null result.

REPRODUCE.md gives ordinary CPU and tracked-job commands, environment versions and exact source/config/input seeds. No external data acquisition or third-party dataset license is involved; generator/config/source hashes define the synthetic data version. All nine positions’ dated source-access/retrieval statements are attributed in provenance/access-inventory.json. None is converted into independent blanket certification.

Figure/table ownership stays with figtab-repo and final report/venue integration with their owners. Use results/confirmatory/summary/, numerical_allowance/, derived/, region_cases.jsonl and this evidence map. The measured case selector was frozen at core K3 trial0/test0; `compbench.conformal.contains_case` evaluates the actual recorded regions. Every table/figure must identify its actual sources and rendering script.

Scope: observed compositions; five synthetic mechanisms; shared fitted center; CPU-run finite study. No latent-probability, label-set, real-data, geometry-specific optimal-center, priority, universal-ranking or arbitrary-shift claim follows.
