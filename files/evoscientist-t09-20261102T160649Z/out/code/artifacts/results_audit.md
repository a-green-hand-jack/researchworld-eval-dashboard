# Results audit: existing Monte Carlo outputs only

## Scope, provenance, and metric definitions

This audit uses only already-run results. No experiments, internet access, paper identification, or source-code edits were performed. Inputs read:

- `/work/artifacts/analysis/summary.csv` — 2,520 aggregate cells.
- `/work/artifacts/analysis/per_seed.csv` — 7,000 fixed-graph cells.
- `/work/artifacts/analysis/paired.csv` — 64 common-record method contrasts.
- `/work/artifacts/analysis/decomposition.csv` — 16 dedicated decomposition checks.
- `/work/artifacts/analysis/validation.json`.
- `/work/artifacts/analysis_protocol.md` and `/work/todos.md` — frozen interpretation and prespecified hypotheses.
- Additionally, `/work/artifacts/analysis/support_summary.csv` — existing full-exposure diagnostics needed to interpret HT.

The validation ledger reports 24,000 assignments across main/size/allocation and 12,000 main assignments. Main contains 840,000 method/mechanism records: 795,259 `ok`, 38,535 `empty_exposure`, 4,106 `rank_failure`, and 2,100 `zero_numeric_propensity`. These are record counts, not independent replications of every scientific contrast. Pilot results are excluded. This is a summary-output audit, not an independent recomputation from assignment-level raw data.

For error e = estimate minus analytically evaluated finite-population GATE, **bias** is mean(e), **MSE** is mean(e²), and **RMSE** is sqrt(MSE), each conditional on a valid estimate. **Availability** is valid/attempts. **Coverage** is the fraction of valid intervals containing GATE, accompanied by its own denominator. The stored **conditional_bias** is the mean assignment-specific noise-conditional bias b; **mean_squared_bias** is mean(b²), not mean(b)². **mean_variance** averages the corresponding noise-conditional contrast variance v.

MCSEs follow the frozen protocol: SD(e)/sqrt(N) for bias; SD(e²)/sqrt(N) for MSE; MSE_MCSE/(2 RMSE) for RMSE. Tables retain original CSV decimal values; any derived confidence limits or ratios are explicitly identified. An entry `value (MCSE)` is not a 95% interval: its approximate pointwise 95% MC interval is value ± 1.96 MCSE, subject to adequate tail sampling. Coverage/availability intervals below are stored 95% Wilson intervals. For paired methods, delta_MSE = mean(e_a² − e_b²) on common valid `(graph_seed, rep)` records within the same design. Different designs and different suites are not paired; their contrast MCSE is the square root of the sum of squared marginal MCSEs.

Synthetic main cells generally have 300 attempts per seed 11/23/37; allocation/size cells have 200. Public-graph main cells have 300 attempts on a single fixed graph. MC uncertainty describes repeated assignments/noise on these fixed graphs, **not a graph-population confidence interval**. Reported seed ranges are descriptive sensitivity, also containing MC variation. Prespecified comparisons below are descriptive checks of the frozen hypotheses, not formal confirmatory superiority tests. The broad decomposition scan in finding 8 is exploratory. No p-value search is used; simultaneous normal-reference diagnostic envelopes are supplied for that many-cell scan rather than interpreting pointwise excursions as discoveries.

## Eight supported findings and limits

### 1. Balanced p=.5 quadratic results do not generalize to p=.2/.8

**Cell keys:** method=`Add`, mechanism=`quadratic`, design=`bernoulli`, n=1000. At p=.5 the suite is `main`; at p=.2/.8 it is `allocation`. All attempts are valid.

| Graph | p | N | Bias (MCSE) | RMSE (MCSE) | Mean conditional bias |
|---|---:|---:|---|---|---:|
| regular32 | .5 | 900 | -0.005430500711867512 (0.011942091522499108) | 0.35782734065953853 (0.008506121864791282) | 0.00012450325507983042 |
| regular32 | .2 | 600 | -0.557505748942786 (0.01865046488818866) | 0.7204024745057598 (0.017174960564863565) | -0.5816712783478502 |
| regular32 | .8 | 600 | 0.5921666768839827 (0.01959071317104188) | 0.7616373737453043 (0.01784767305925504) | 0.5817079720293475 |
| ws32 | .5 | 900 | -0.0006337454231252752 (0.012065850417046033) | 0.36138849525494815 (0.008801234560151661) | 0.0013884680749667567 |
| ws32 | .2 | 600 | -0.6053542484279415 (0.019163619277951325) | 0.7653325123096176 (0.01669687150681376) | -0.5839753329116446 |
| ws32 | .8 | 600 | 0.6039967660263353 (0.019876631512907705) | 0.7750709621549271 (0.01776875088429875) | 0.5840304305633665 |

For regular32, derived unpaired bias differences relative to .5 are **-0.5520752482309186**, MCSE **0.022146182300281536**, pointwise 95% MC interval **[-0.5954817655394704, -0.5086687309223668]**, and **0.5975971775958502**, MCSE **0.022943617685138036**, interval **[0.5526276869329796, 0.6425666682587208]**. The corresponding RMSE ratios are **2.0132683913362563** and **2.128505251559238**. Different suite streams preclude a paired allocation contrast.

The near-zero balanced average is not absence of conditional transport error: regular32 mean(b²) is **0.0009980140756138307** at .5 versus **0.33901011031416195** at .2 and **0.3390507779672757** at .8. Cluster randomization also retains the sign reversal: regular32 Add quadratic bias is **0.022023054938929146** at .5, **-0.46528889823157327** at .2, and **0.4695073063289649** at .8.

**Seed sensitivity:** regular32 Bernoulli Add quadratic RMSE ranges, rounded to six decimals, are .335516–.375329 at .5, .703518–.732209 at .2, and .726442–.808179 at .8. Every seed has negative bias at .2 and positive bias at .8; the allocation pattern is not driven by just one graph seed. Near-zero pooled bias at .5 supports a balanced-design cancellation interpretation, not general robustness to quadratic misspecification.

**Sources:** `summary.csv` and `per_seed.csv`, keys above; frozen allocation sensitivity in `/work/todos.md`.

### 2. Additional correct features can be dramatically variance-inflating

**Cell keys:** `main`, Bernoulli p=.5, `linear` mechanism, n=1000, all 900/900 valid. Both feature sets contain the correct linear mean; the extra quadratic features do not supply a missing signal term here.

| Graph | Method | RMSE (MCSE) | Mean conditional variance |
|---|---|---|---:|
| regular32 | Add | 0.35564997416337235 (0.008482396860050973) | 0.13733675832123937 |
| regular32 | Quad | 1.5050043140568352 (0.034199573753521874) | 2.371503237872983 |
| regular128 | Add | 0.7765404663337832 (0.018590145193857172) | 0.5951621928870794 |
| regular128 | Quad | 6.871758554475069 (0.1650565646001778) | 45.83618428887159 |

Derived variance ratios Quad/Add are **17.267796814643656** and **77.01461019646476**. The same-assignment Quad−Add paired delta_MSE is **2.138551081207277**, MCSE **0.1023680167796309**, N_common=900, derived 95% MC interval **[1.9379097683192004, 2.3391923940953534]** at regular32; and **46.6180505351474**, MCSE **2.2670532858000523**, N_common=900, interval **[42.174626094979295, 51.061474975315498]** at regular128. Conditional biases are numerically near zero, so this is a variance cost, not a bias correction.

**Seed sensitivity:** regular128 Bernoulli linear RMSE ranges, rounded to six decimals, are .732651–.819944 for Add and 6.708386–6.990810 for Quad; each of the three seeds shows the large inflation. A correct richer mean model is not sufficient for a stable endpoint contrast. Add–Quad also changes arm-specific terms, so it is not an isolated quadratic-term ablation; the variance-inflation direction also holds using Lin as the simpler separate-arm comparison in the same source cells. The .5 quadratic-mechanism results in finding 1 should not be presented as evidence that Quad necessarily improves RMSE either.

**Sources:** `summary.csv`, `per_seed.csv`; `paired.csv`, `(regular32/regular128, bernoulli, linear, Quad, Add)`.

### 3. On public graphs, count versus fraction is consequential and mechanism-dependent

To isolate exposure parameterization better than Count−Add, compare `Count` against the separate-arm fraction model `Lin`. Below: `main`, Bernoulli p=.5; all methods have 300/300 valid records on each fixed public graph.

| Graph | Mechanism | Fraction Lin RMSE (MCSE) | Count RMSE (MCSE) |
|---|---|---|---|
| ego | count | 0.7752567109558257 (0.009317314295545472) | 0.04845689808342395 (0.0018336409246478968) |
| stanford | count | 0.9006100458686618 (0.003961191355523686) | 0.03265511346205508 (0.0012540989834110897) |
| ego | linear | 0.10900570796552202 (0.004295194487591785) | 0.9686990603737996 (0.0029211494120731534) |
| stanford | linear | 0.06342853430922385 (0.0025916589935848964) | 0.9802666977376412 (0.0019198207498472084) |

For the count mechanism, Lin bias is **-0.7575944674480324** (MCSE **0.00951562537803168**) on ego and **-0.8980007063484169** (MCSE **0.0039618524252917585**) on Stanford; Count bias is **0.002023407613985156** (MCSE **0.0027998905816502997**) and **-0.0008071173209200984** (MCSE **0.0018879170423235032**), respectively. The performance ordering reverses for the fraction-linear mechanism: count is not a universal improvement.

The supplied paired table compares Count against Add, not Lin. For the count mechanism, Count−Add delta_MSE is **-0.5988466737090152** (MCSE **0.014399103455390585**, N_common=300) on ego and **-0.8099754477886809** (MCSE **0.00712813173745313**, N_common=300) on Stanford, both Bernoulli. Derived pointwise 95% MC intervals are **[-0.62706891648158081, -0.57062443093644966]** and **[-0.8239465859940891, -0.79600430958327273]**. Cluster Count−Add differences also favor Count for this mechanism: **-0.20063398136047864** (MCSE **0.007591888363465173**) and **-0.6789575371725017** (MCSE **0.006701683750579771**), each N_common=300. These paired effects should not be mislabeled as pure Count−Lin effects; covariance needed for that paired MCSE is absent from the supplied summaries.

**Limits:** these are two fixed public graphs, not graph-seed replications or evidence of performance on a sampled public-network population.

**Sources:** `summary.csv`, `(main, ego/stanford, bernoulli, .5, Lin/Count, count/linear)`; `paired.csv`, count contrasts for both designs.

### 4. Correlated-noise interval failure is substantial; known covariance largely isolates it

**Cell keys:** `main`, method=`Add`, mechanism=`correlated`, p=.5. Every estimate and interval in these cells is available. Stored coverage fractions and Wilson limits:

| Graph/design | N_intervals | iid-regression coverage [95% Wilson] | Known-covariance coverage [95% Wilson] |
|---|---:|---|---|
| ego/Bernoulli | 300 | 0.48 [0.42407680086272237, 0.5364289179862594] | 0.95 [0.9191529665272558, 0.9694683593706526] |
| ego/cluster | 300 | 0.51 [0.45366418945602693, 0.5660829511194823] | 0.97 [0.9439774608583589, 0.9841381461905676] |
| stanford/Bernoulli | 300 | 0.8733333333333333 [0.8309188299507383, 0.9063077515349339] | 0.9466666666666667 [0.9151308582251686, 0.9669080874809034] |
| stanford/cluster | 300 | 0.7866666666666666 [0.7368372921361543, 0.8292474043617724] | 0.95 [0.9191529665272558, 0.9694683593706526] |
| regular8/Bernoulli | 900 | 0.8588888888888889 [0.834616269172565, 0.8801108477300851] | 0.9455555555555556 [0.928749313436297, 0.9585744446998103] |
| regular8/cluster | 900 | 0.81 [0.7830732079831068, 0.8342917010442598] | 0.9511111111111111 [0.9350057089849871, 0.9633819364096751] |

For these correct-mean cells, mean conditional bias is numerically near zero. On ego/Bernoulli, the marginal coverage difference is .47; do not invent a paired coverage-difference interval, because joint hit counts are not supplied. Known-covariance marginal intervals are compatible with .95 in all listed cells. This supports covariance misspecification as the principal issue here, not universal validity of ordinary intervals. Coverage integrates fresh Gaussian noise schedules on fixed graphs; it is not a design-based validity claim conditional on one fixed realized outcome schedule, and known covariance is an oracle diagnostic, not an estimated-covariance procedure.

**Sources:** `summary.csv`, keys above; noise/interval interpretation in `/work/artifacts/analysis_protocol.md`.

### 5. Cluster design is not uniformly superior, even when estimate availability is complete

**Cell keys:** `main`, ba32, n=1000, p=.5, Add, quadratic; both designs have 900/900 valid estimates. Bernoulli RMSE is **0.3138351024546008** (MCSE **0.007587153664041823**); cluster RMSE is **0.37754149922639324** (MCSE **0.009750337404913868**). MSEs are **0.09849247153268977** and **0.14253758363811267**, respectively.

The derived **unpaired** cluster−Bernoulli delta_MSE is **0.044045112105422904**, MCSE **0.008768266925140739**, pointwise 95% MC interval **[0.026859308932147056, 0.061230915278698755]**. This is a prespecified design-audit example, not a familywise superiority claim. Conditional variance actually decreases, from **0.10440367249985429** to **0.0920099283977006**, but mean(b²) increases from **0.0015261235493367487** to **0.04157446265481291**. Improving endpoint support or variance alone need not improve total error.

**Exact per-seed RMSE cells:**

| ba32 graph seed | Bernoulli | Cluster |
|---:|---:|---:|
| 11 | 0.3213324526235146 | 0.3955892248936147 |
| 23 | 0.3180856679283354 | 0.358646965345991 |
| 37 | 0.3017356083520981 | 0.377484132528135 |

The direction repeats across these three fixed graphs, but the design streams are independent even within a graph seed. No paired design MCSE is justified. Availability can also worsen under clustering (next finding), so neither support nor RMSE is uniformly improved.

**Sources:** `summary.csv` and `per_seed.csv`, keys above; independent streams stipulated in `/work/artifacts/analysis_protocol.md`.

### 6. Availability conditioning is scientifically material, not a removable implementation detail

For `main`, p=.5, Oracle/threshold:

| Graph/design | Valid/attempts | Availability [95% Wilson] | Conditional RMSE (MCSE) |
|---|---:|---|---|
| regular32/Bernoulli | 210/900 | 0.23333333333333334 [0.20686981177940703, 0.26206359980995514] | 0.9493685697577552 (0.04972018684665685) |
| regular32/cluster | 897/900 | 0.9966666666666667 [0.9902457886548788, 0.9988657322599341] | 0.37420297914338324 (0.011435931417841308) |
| regular128/Bernoulli | 0/900 | 0.0 [4.336808689942018e-19, 0.004250146730054126] | unavailable, not zero |
| regular128/cluster | 51/900 | 0.056666666666666664 [0.0433606290045125, 0.07374116776280214] | 0.6900926628433368 (0.08604219573459035) |

The negligible nonzero lower Wilson endpoint at 0/900 is floating-point residue and should be interpreted as zero. Failures in these cells are rank failures. For regular128/cluster, seed 11/23/37 valid counts are **14/16/21** out of 300 each; conditional RMSE is **0.4005413443583107 / 0.7857346777428716 / 0.76106101214443**, respectively. Selection and MC noise at such small denominators make the pooled successful-fit RMSE a poor summary of practical reliability.

The regular32 Bernoulli Oracle−Add threshold paired contrast uses only **N_common=210**, delta_MSE **-0.09634664188310721**, MCSE **0.09995769577732819** (pointwise MC interval spans zero). It does not compare an always-available Oracle with Add on all 900 attempts. At regular128/Bernoulli N_common is **0**, so the corresponding effect is unidentifiable from these runs. At ba32, clustering reduces Oracle/threshold valid count from **799/900** to **666/900**. For Hajek80/linear, regular32/Bernoulli has **11/900** valid and **889** empty-exposure failures; regular128 has **0/900** valid under either design. Such successful subsets must never be assigned zero loss for failures. Fractional Hájek also need not target the global endpoint contrast under misspecification.

**Pooling qualification:** equal numbers of attempted assignments per graph seed do not imply equal graph weights after conditioning on success. For regular32/Bernoulli Oracle/threshold, valid counts are **67, 66, 77**. The supplied pooled RMSE **0.9493685697577552** equals the valid-count-weighted mixture; the derived equally weighted mean of the three per-seed conditional MSEs gives RMSE **0.9508342541827324**. Thus describe the summary as an equal-attempt fixed-graph mixture conditioned on validity, not an unqualified equal-weight average of per-seed conditional risks. Different methods can condition on different assignment and graph-seed subsets.

Rank filtering is feature-only. An unconditional Bernoulli visibility bound is not a probability bound conditional on rank acceptance. For example, validation.json's regular128 threshold-visibility union bound is **9.66670199239399e-10**, but it cannot be transferred unchanged to rank-selected fits or to cluster randomization.

**Sources:** `summary.csv`, `per_seed.csv`, `paired.csv` (threshold Oracle−Add), `validation.json`, and `/work/artifacts/analysis_protocol.md`.

### 7. HT all-zero estimates and heavy tails invalidate naive finite-MC precision claims

**Cell keys:** `main`, HTfull, linear, p=.5. Bernoulli regular32, regular128, sbm32, and ws32 each have **900/900 valid**, **zero_estimate_fraction=1.0**, empirical **bias=-2.0**, **RMSE=2.0**, and both empirical **bias_mcse=0.0** and **rmse_mcse=0.0**. Regular128/cluster has the same all-zero result. These are finite-sample facts, **not evidence that the exact local one-hop HT estimator is truly biased or that MC uncertainty is absent**.

The existing support table records **full_treated_mean=0.0** and **full_control_mean=0.0** for each of these all-zero graph/design cells: no sampled full-neighborhood events. For regular32/Bernoulli, minimum full-exposure probability remains **1.1641532182693479e-10**, and for regular128/Bernoulli **1.4693679385278594e-39**. Rare events with enormous inverse probabilities are absent from the realized sample; an empirical zero SE cannot quantify the unseen tail. Do not report a [2,2] RMSE interval as meaningful precision or rank HT against regression on that basis.

Observed heavy-tail examples:

| Graph/design | N_valid | Zero-estimate fraction | Bias (MCSE) | RMSE (MCSE) | Maximum absolute error |
|---|---:|---:|---|---|---:|
| regular32/cluster | 900 | 0.058888888888888886 | 0.06834950602439777 (2.1463815564266233) | 64.36077271626367 (32.01018095494735) | 1925.70326512468 |
| ba32/Bernoulli | 900 | 0.9977777777777778 | -1.7519231130257185 (0.24765721249676337) | 7.629441517149416 (3.5526780762773624) | 220.8911706763719 |
| ba32/cluster | 900 | 0.8344444444444444 | 1.117779423805371 (1.7917187597058735) | 53.73618040576695 (24.858080512973643) | 1549.7776097982817 |

Normal and delta-method MC intervals can be unreliable even where their estimated SE is nonzero. In Stanford/Bernoulli, HTfull has **0/300 valid** and **300 zero_numeric_propensity** records per mechanism, accounting for **2,100** main records over seven mechanisms. The support table has min_full_prob=0.0 there: this is numerical underflow, not structural positivity failure, despite nonzero observed exposure counts. Exact one-hop HT interpretation also must not be extended to a nonlocal two-hop mechanism.

**Sources:** `summary.csv`, HTfull/linear cells; `support_summary.csv`, corresponding main graph/design cells; `validation.json`; HT restrictions in `/work/artifacts/analysis_protocol.md`.

### 8. The conditional MSE decomposition appears MC-consistent, with necessary qualifications

The correct check is **gap = mean(e² − b² − v)** on the same valid records, standardized by **gap/MCSE**, not comparison of MSE with mean(b)² + mean(v). From the supplied summaries, `mse − mean_squared_bias − mean_variance` reproduces `decomposition_gap` up to maximum absolute floating-point discrepancy **2.7284841053187847e-12** over finite cells. This checks arithmetic consistency of stored aggregates, not independent raw-row alignment.

The dedicated `decomposition.csv` matches the main Add/linear graph/design cells and all **16/16** have |gap/MCSE| < 1.96. Standardized gaps, derived and rounded to six decimals:

| Graph | Bernoulli gap/MCSE | Cluster gap/MCSE |
|---|---:|---:|
| regular8 | 1.307884 | 0.759947 |
| regular32 | -1.799041 | -1.360215 |
| regular128 | 0.271965 | 1.388814 |
| sbm32 | -1.252657 | -0.108585 |
| ba32 | -1.538843 | 0.992274 |
| ws32 | -1.316192 | 1.589198 |
| ego | -0.575952 | -1.317470 |
| stanford | -0.175272 | -0.547524 |

The largest absolute dedicated ratio is **1.7990408017513844**, regular32/Bernoulli: gap **-0.010849854198831946**, MCSE **0.006030910576496933**, derived pointwise 95% MC interval **[-0.022670438928765933, 0.0009707305311020421]**. All dedicated cells also lie inside a Bonferroni simultaneous 95% normal-reference MC envelope with critical |gap/MCSE| **2.955166847497834** for 16 checks.

**Exploratory broader stress check:** across all suites, **2,354** aggregate cells have finite positive decomposition MCSE; **133** exceed |gap/MCSE|=1.96 (derived proportion **0.05649957519116398**). The largest absolute ratio is **3.5616892017357094** at `(size, regular128, n=500, cluster, p=.5, Oracle, quadratic)`, with gap **-0.4043010851277582**, MCSE **0.11351385879787915**. Therefore it would be false to say every decomposition cell is within two MCSE. However, the maximum is below the Bonferroni simultaneous 95% normal-reference threshold **4.251435780971337** for 2,354 checks. Many cells share assignments or are duplicates across mechanisms; do not treat the exceedance count as independent binomial data. These are approximate MC diagnostic envelopes, not a formal significance search, proof of the identity, or assurance that rare tails are adequately sampled.

**Supported wording:** the dedicated main Add/linear checks are consistent with the conditional decomposition at reported MC precision; a many-cell exploratory scan shows ordinary pointwise excursions but no simultaneous normal-reference discrepancy. Do not turn this into a claim of unconditional or universally stable MSE estimation. Ridge uses direct b²+v rather than the OLS residual identity.

**Sources:** `decomposition.csv`, `summary.csv`, and the decomposition rule in `/work/artifacts/analysis_protocol.md`.

## Interpretation and next steps (not executed)

The strongest story is an error audit: balanced-design cancellation can hide misspecification; a richer correct mean can amplify endpoint variance; count/fraction parameterization matters on irregular public graphs; covariance errors and availability are separate from point-estimation bias. Neither clustering nor any fixed feature map is uniformly superior. Keep the conditional denominators, graph-seed ranges, and HT tail warning adjacent to performance claims.

Future-only validation recommendations, outside this analysis-only task:

- Before making graph-population claims, use independent additional graph realizations and cluster partitions, retaining separate fixed-graph MC and between-graph uncertainty.
- Before ranking HT, use a prespecified rare-event-aware evaluation or exact moment calculation where feasible; ordinary additional finite-MC draws and naive SEs are not an adequate tail diagnostic.

## Deliverable

`/work/artifacts/results_audit.md` contains the audit and embedded numerical tables. No separate plots were requested or produced; existing CSVs are unchanged. All requested priority findings are represented above, with exploratory versus prespecified interpretation separated.
