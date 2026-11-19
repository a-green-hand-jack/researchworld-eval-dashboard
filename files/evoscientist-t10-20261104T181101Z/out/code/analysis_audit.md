# Independent analysis audit of completed experiments

## Bottom line

The saved summaries are internally consistent, and the declared multiplicity corrections reproduce. **No confirmed numerical or aggregation bug was found in the checks performed.** There are genuine finite-sample Wald failures, a severe shift/clipping pathology, and important limits on the efficiency claims. The strongest supported result is a **setting-specific sharp-tail width improvement**, not general superiority of safeCP. The exact-family minimum observed coverage, 0.943333, is not a contradiction of a ≥0.95 coverage guarantee.

No browsing, experiment execution, predictor fitting, or edits to existing code/data were performed. The only executable added is a read-only analysis script. Interpret “confirmatory” below as **within the family declared locked in the supplied manifest**; these files alone cannot independently establish when the lock occurred.

## 1. Scope, integrity, and metrics

Primary inputs: `/work/{summary.csv,paired.csv,seed_summary.csv,integrity_audit.json,multiplicity_manifest.json,data_eda.json,design_addendum.md}`. Existing implementation was read, not executed, to interpret mechanisms. Six selected existing raw main-result files and their diagnostics were checked: cells **10, 18, 22, 23, 34, 37** (252,000 main-method output rows). This is not an independent reread of all 1,656,000 raw rows or of the supplemental raw files.

**Row convention:** `summary.csv:L173` means physical CSV line 173, including header line 1; it has key `(cell_id=10, method=safe_cp)`. Keys remain authoritative if files are reordered. Artifact tables preserve these locators.

- 39 cells × 16 methods = **624 summary rows**; **1,248 paired rows**; **1,872 seed rows**.
- 30 cells have 3,000 repetitions and nine sensitivity cells have 1,500: **103,500 trial inputs**, each evaluated by 16 correlated methods, giving **1,656,000 method-output rows**. Do not treat method-output rows as independent trials. The two Hoeffding methods contribute 207,000 descriptive supplemental rows.
- Coverage: `hits/reps`, the fraction of intervals containing the saved target. Wilson95 is a **pointwise descriptive Monte Carlo interval**, not the method's inferential guarantee.
- Mean width: average `high-low`, after the declared clipping; MCSE is sample SD divided by √reps. This measures average reported interval length, **not validity** or per-dataset uncertainty.
- Paired width effect: Δ = mean(width_A − width_B); MCSE = SD(width_A − width_B)/√reps. Ratio = mean(width_A)/mean(width_B), **not mean of trialwise ratios**. Its paired delta-method MCSE is SD(width_A − ratio·width_B)/(√reps·mean(width_B)). Reported ratio95 intervals and the additional Δ ± 1.96 MCSE intervals are **pointwise, not simultaneous**.
- Undercoverage test: exact binomial lower tail `P_{p=.95}(H ≤ observed hits)`, with Holm correction over the declared 252 hypotheses. It tests the composite null coverage ≥.95 at its boundary.

Independent summary-level checks recovered every hit count from seed summaries exactly and mean widths within 6.67e−13. Coverage, Wilson bounds, simultaneous CP bounds, and coverage p-values reproduce within 5.0e−13; paired t p-values within 1.3e−12. Ratios/ratio intervals differ by at most 9.1e−10 from formulas using rounded CSV entries. Selected raw checks reproduce endpoint coverage, degeneracy, mean widths, width MCSEs, and paired MCSEs within 4.4e−11. Counts, endpoint checks, and pairing in the full integrity JSON are consistent with these checks, but its `verified=true` fields are not independent proof of all raw computations.

## 2. Exact coverage: what the .943 minimum does and does not mean

The locked MC family is **five feasible exact methods × 36 nonshift cells = 180**. For each, the saved simultaneous lower bound is

`L = Beta^{-1}(.05/180; hits, reps−hits+1)`.

Under independent Monte Carlo repetitions within each cell, Bonferroni yields **at least 95% simultaneous confidence that all 180 true repeated-sampling coverage probabilities exceed their respective L values**. Dependence between methods/cells does not invalidate Bonferroni. This is confidence about the simulation's coverage probabilities, not an exact guarantee obtained from observed coverage.

| Finding | Exact row/key locator | Result |
|---|---|---|
| Minimum exact-family observed coverage | `summary.csv:L99`, cell 6, smooth_u, n=100/N=2000, label_cp | 2830/3000 = **.943333**; Wilson95 **[.934479,.951054]**; simultaneous lower **.927341** |
| Other exact rows below .95 | `summary.csv:L531`, cell 33, forest n=100, label_cp; `L595`, cell 37, galaxies n=500, label_cp | **.944333**, **.949000**, respectively; both Wilson intervals include .95 |
| SafeCP minimum observed coverage | `summary.csv:L573`, cell 35, forest n=2000 | **.983667**, not .943333 |
| SafeCP minimum simultaneous lower bound | `summary.csv:L429`, cell 26, affine sensitivity n=500/N=50000 | **.973159** |

Only **three of 180** empirical coverages fall below .95, all labeled CP. At the minimum row, the nominal-boundary undercoverage p-value is **.0532631**, before multiplicity correction; thus even this unadjusted test does not reject coverage ≥.95. An explicitly exploratory Holm screen over all 180 exact rows has minimum adjusted p=1.

**Correct interpretation:** the simultaneous empirical lower bound for the minimum coverage across the family is **.927341**, not .95. **148/180** individual simultaneous lower bounds exceed .95, including all 144 rows for the four non-label exact methods. Failure of the other lower bounds to exceed .95 is not proof of undercoverage. A theoretical coverage probability ≥.95 does not force a finite Monte Carlo hit rate ≥.95.

**A mild anomaly worth retaining, not concealing:** exact binomial summation under the saved smooth_u truth .35 gives actual labeled-CP coverage **.954256** at n=100. Observing ≤2830 hits then has probability **.003105**. Across an exploratory diagnostic family of all 36 nonshift labeled-CP cells, Holm gives **.111783** for this row. It is somewhat low relative to the actual CP acceptance probability, but not family-significant; it does not establish a sampling/CP bug. No new samples were generated for this calculation. See `/artifacts/analytic_label_cp_diagnostic.csv`.

The mathematical guarantee remains conditional on the stated sampling/fixed-partition assumptions and correct implementation. Outward padding is not a formal verification of special-function floating-point error (`design_addendum.md:L9`; `intervals.py:L1–4`). Do not describe simulation consistency as a proof of the theorem.

## 3. Confirmatory width comparisons and effect sizes

The declared tests are **safe_cp vs ppi_pp** and **cp_tails vs label_cp**, each over 36 nonshift cells: **72 one-sided paired t tests**, Holm-adjusted jointly. Rejection concerns smaller **expected reported width only**. There are **nine rejections**: four for safeCP and five for tails CP, **all in sharp_tails**. The other 63 adjusted p-values are 1; that is not evidence of equal width.

All nine are listed below. CIs are pointwise MC ratio intervals. Apart from the first safeCP row, stored adjusted p-values underflow to zero; interpret them as extremely small, **not literal p=0**.

| Cell; n/N | Pair A/B | Width ratio [pointwise MC95] | `paired.csv` line |
|---|---|---|---|
| 9; 100/2000 | safe_cp / ppi_pp | .973851 [.971400,.976301] | L312; Holm p=3.96885e−89 |
| 10; 500/10000 | safe_cp / ppi_pp | **.734872 [.732548,.737196]** | L344 |
| 11; 2000/40000 | safe_cp / ppi_pp | .665796 [.664213,.667379] | L376 |
| 29; 500/50000 | safe_cp / ppi_pp | .554093 [.550784,.557402] | L952 |
| 9; 100/2000 | cp_tails / label_cp | .776123 [.773898,.778348] | L309 |
| 10; 500/10000 | cp_tails / label_cp | **.602113 [.600047,.604179]** | L341 |
| 11; 2000/40000 | cp_tails / label_cp | .556957 [.555601,.558314] | L373 |
| 28; 500/2500 | cp_tails / label_cp | .874499 [.871691,.877307] | L917 |
| 29; 500/50000 | cp_tails / label_cp | .451239 [.448302,.454176] | L949 |

### Sharp tails n=500: impressive, but explainable and specialized

`summary.csv:L173` (safe_cp) has width **.0643527**, MCSE **.000103714**, and **3000/3000** coverage. PPI++ (`L165`) has width **.0875700**, MCSE **.00000314554**, coverage **.952333**, Wilson95 **[.944114,.959396]**.

- SafeCP width reduction is **26.51%**, pointwise MC95 **[26.28%,26.75%]**. Paired Δ=**−.0232173**, pointwise MC95 **[−.0234209,−.0230137]** (`paired.csv:L344`).
- Tails CP width is **.0537950** (`summary.csv:L171`) versus labeled CP **.0893437** (`L163`): reduction **39.79% [39.58%,40.00%]**, paired Δ=**−.0355487**, pointwise MC95 **[−.0357333,−.0353640]** (`paired.csv:L341`).
- Observed 100% coverage means **zero misses in 3,000 trials**, not true coverage=1. Its Wilson95 is **[.998721,1]**, and the locked simultaneous CP lower bound is **.997274**.

The score/response relationship is symmetric and almost deterministic in the prespecified tail partition: `p(Y=1|S)=.005+.99·1{S<.25 or S≥.75}` (`run_experiments.py:L33–34`). A scalar linear score control has zero population covariance here, whereas the tail indicator is highly informative. Existing diagnostics (`results/10_sharp_tails_n500_N10000_diagnostics.csv.gz`, all `(seed,rep)` rows) show mean PPI++ lambda **−.0001199** and **safe_choice=2 (tails) in all 3000 trials**. This supports the nonlinear-partition explanation, not a claim that finite-sample exact methods generally beat PPI++.

The unlabeled sample matters: at sharp_tails n=500, safeCP/PPI++ ratios are **1.291765** at N=500 (`paired.csv:L888`), **1.060918** at N=2500 (`L920`), .734872 at N=10000, and .554093 at N=50000. Tails CP improves on labeled CP already at N=2500, but safe selection's additional error allocation delays the crossover. No global crossover threshold is estimated.

## 4. Real-data results: no practical width advantage demonstrated

These are **with-replacement empirical-population experiments**, not new independently collected datasets or deployment validation (`run_experiments.py:L45–50,L82–88`; `design_addendum.md:L3`). Forest has 1,596 records, target .151629, score/label correlation .537487; galaxies has 16,743 records, target .259273, correlation .740783 (`data_eda.json`, objects `dataset=forest` and `dataset=galaxies`). Large simulated n or N does not create new unique source observations. MC intervals condition on these fixed populations/predictions; they do not quantify population-sampling or predictor-training uncertainty.

| Dataset; n/N | SafeCP width / coverage | PPI++ width / coverage | Width ratio [pointwise MC95] | Locators |
|---|---|---|---|---|
| Forest; 500/10000 | .0817321 / .992667 | .0534596 / .945000 | **1.528857 [1.526967,1.530748]** | summary L557,L549; paired L1112 |
| Galaxies; 500/10000 | .0994249 / .990667 | .0530900 / .944000 | **1.872761 [1.869944,1.875577]** | summary L605,L597; paired L1208 |

Across all three n values, safeCP is **51.3–54.8% wider** on forest and **86.2–88.4% wider** on galaxies (`paired.csv:L1080,L1112,L1144,L1176,L1208,L1240`). It is also about **25.1–27.1% wider than labeled CP** (`paired.csv:L1081,L1113,L1145,L1177,L1209,L1241`; descriptive, not designated comparisons). At n=500, all 3,000 safe choices are the **selection-adjusted labeled candidate**, in each dataset's existing diagnostics (`34_forest...`, `37_galaxies...`, `safe_choice=0`). Thus the shown feasible exact procedure does not exploit these scores enough to offset its penalties.

This is an efficiency/validity trade-off, not proof that PPI++ is uniformly valid or universally superior: PPI++ at n=100 has significant adjusted undercoverage in **both datasets** (forest `summary.csv:L533`, coverage .922667, Holm p=2.42203e−8; galaxies `L581`, .933667, p=.0113083). At n=500 the undercoverage tests do not reject, but non-rejection does not certify .95 coverage.

## 5. Genuine failure cases and suspicious-looking outputs

### Rare outcomes: a shared zero-label Wald failure, not a width win

At cell 18, rare_tails n=100/N=2000, truth=.01:

- PPI++: **1878/3000=.626000**, Wilson95 **[.608535,.643143]**, width **.0244873**, **1121 degenerate intervals** (`summary.csv:L293`). Holm-adjusted undercoverage p underflows to zero in the locked family.
- Labeled Wald: **.626333**, also 1121 degenerate intervals (`L290`); labeled CP: **.982000**, width .0520764 (`L291`); safeCP: **.996000**, width .0674885 (`L301`).
- Existing raw PPI++ intervals contain exactly **1121 [0,0] intervals**, all misses, and just **one additional nondegenerate miss**. Their trial keys equal the labeled-Wald zero-width keys. Example: `/work/results/18_rare_tails_n100_N2000.csv.gz`, key `(seed=1729,rep=2,method=ppi_pp)` is `[0,0]` at truth .01.

For this generator, iid marginal labels are Bernoulli(.01), so the exact all-zero probability is **.99^100=.366032** (observed zero-label frequency .373667). With all labels zero, fitted covariance/lambda and plug-in variance vanish; the Wald interval becomes [0,0] (`intervals.py:L123–135`). This mechanism explains almost the entire .626 coverage. It is expected failure of the declared Wald convention, not evidence that the counting code is broken. **Do not present the smaller width as successful inference.** Fixed-coefficient PPI does not share the same severe collapse here: coverage **.951333**, width .0694272 (`summary.csv:L292`), which remains simulation evidence, not a finite-sample guarantee.

The problem persists at n=500: PPI++ coverage **.866000**, adjusted p=1.73571e−67 (`summary.csv:L309`). At n=2000 it is .937000 but adjusted p=.198744 (`L325`); do not equate non-rejection with exact validity.

### Shift: clipped zero-width intervals, not efficiency or zero uncertainty

Cell 22, shift n=500/N=10000, PPI++ has width **.000775284** (rounds to .0008), MCSE **.0000895068**, and **0/3000 coverage** (`summary.csv:L357`). Existing raw outputs show **2883/3000=96.1% are [1,1]**, not genuinely zero-variance estimates; the remaining 117 also miss. Example: `/work/results/22_shift_n500_N10000.csv.gz`, `(1729,0,ppi_pp)` is `[1,1]`, truth .5. At n=2000 all 3000 intervals are [1,1], mean width=0 (`summary.csv:L373`; corresponding cell-23 raw file).

The implementation clips both endpoints (`intervals.py:L66–70`). Labeled scores are Uniform(0,1), unlabeled scores Beta(4,1), while the target stays the labeled mean .5 (`run_experiments.py:L27–28,L40–52`). For n/N=.05, the population pooled score variance is .0334467, lambda limit **2.135593**, and the untruncated estimator center limit is **.5+lambda·(.8−.5)=1.140678**. Saved mean lambda is **2.135655** at n=500, matching this explanation. The pathology is misspecification/extrapolation amplified by endpoint clipping, not legitimate precision.

This is outside the same-distribution assumptions and excluded correctly from all three locked families. SafeCP's observed coverage here (.989333 at n=500; `summary.csv:L365`) is **not a general shift-robustness guarantee**. It chose the adjusted labeled candidate in all 3000 trials of the checked cell. For tails CP, the labeled conditional response means in both the symmetric tail group and its interior complement equal .5 under this affine model; reweighting these equal means does not change the target. The unlabeled tail mass actually changes from .5 to **.6875** under Beta(4,1), so its good coverage is not evidence of correct transported masses or general transport validity. Labeled-only CP itself does not require an unlabeled-distribution assumption.

At cell 23, **all 16 paired ratios with reference ppi_pp are undefined**, including 0/0 for PPI++ itself. They are correctly NaN, not zero/infinite or dropped trials (`paired.csv:L738,L740,...,L768`). Label these explicitly in any table. Do not rank methods using these ratios.

### Other undercoverage findings

There are **31/252 Holm-significant undercoverage tests**: labeled Wald 4, PPI++ 5, half Wald 4, tails Wald 5, four-bin Wald 5, eight-bin Wald 8; fixed-coefficient PPI 0. All row locators are in `/artifacts/asymptotic_undercoverage_audit.csv`. Eight-bin Wald on forest/galaxies n=100 reaches **.895/.893 coverage** (`summary.csv:L537,L585`). This is a material finite-sample warning against choosing more bins by width. Fixed-bin fitted means do not automatically require cross-fitting, and these results alone do not diagnose data leakage; sparse/degenerate Wald behavior is a different issue.

## 6. Seed variation and uncertainty

Seeds are **1729, 2027, 7919**. Main/empirical seed blocks contain 1000 trials each; sensitivity blocks contain 500. Seed summaries aggregate exactly to reported hits and widths. The unit of MC replication is the independent trial, not just three seed blocks; pooled MCSEs are not estimates of performance variation across trained models or independent real populations.

| Cell/method | Coverage by seed (1729,2027,7919) | Width or ratio variation | `seed_summary.csv` locator |
|---|---|---|---|
| Smooth_u n=100 label_cp | .946, .942, .942 | widths .193416–.193696 | L293–295 |
| Sharp_tails n=500 safe_cp | 1, 1, 1 | widths .064317, .064543, .064199; safe/PPI++ ratios .734471, .737035, .733110 | safe L515–517; PPI++ L491–493 |
| Rare_tails n=100 ppi_pp | .632, .618, .628 | widths .024690, .024359, .024412 | L875–877 |
| Shift n=500 ppi_pp | 0, 0, 0 | widths .000810, .000665, .000851 | L1067–1069 |
| Forest n=500 safe / PPI++ | safe .991,.995,.992; PPI++ .947,.936,.952 | width ratios 1.527846,1.526853,1.531880 | safe L1667–1669; PPI++ L1643–1645 |
| Galaxies n=500 safe / PPI++ | safe .988,.992,.992; PPI++ .940,.940,.952 | ratios 1.872246,1.874384,1.871652 | safe L1811–1813; PPI++ L1787–1789 |

The central conclusions have the same direction in every seed. This is useful robustness evidence, not three independent dataset validations. Coverage has visibly more MC variation than widths: at p=.95, the Bernoulli MCSE for a 1000-trial block is .00689. Galaxies labeled CP n=500 ranges **.937–.963** across seeds (`L1781–1783`); selecting only the worst seed would be misleading. No confirmatory between-seed heterogeneity test was specified.

## 7. Corrections, unsupported claims, and next actions

### Corrections needed in interpretation/reporting, not a reason to alter saved results

1. **Do not conflate guarantees with empirical coverage.** Replace “every exact empirical coverage ≥95%” with “the exact procedures have a stated ≥95% guarantee under assumptions; observed family minimum was 94.33%, consistent with MC variation after accounting for selection.” Also report the family minimum simultaneous lower bound **92.734%**, not “MC certified ≥95% throughout.”
2. **Do not claim universal or real-data efficiency gains.** Only nine designated width comparisons reject, all sharp_tails. Real data show substantial penalties, including penalties relative to labeled CP. Width comparisons alone cannot establish valid-method superiority or coverage equivalence.
3. **Treat [0,0] rare-event and [1,1] shift intervals as failure diagnostics.** `degenerate` currently conflates zero-variance collapse with clipping-induced point intervals. Separate these concepts in prose; untruncated endpoints/centers and numerical-fallback counts are not available in the requested summaries. Existing raw endpoints diagnose the examples, but do not recover every preclipping quantity.
4. **Known-mass ablation is confounded.** `intervals.py:L57–62` changes both mass knowledge and response error allocation: known masses use error/K for responses; unknown masses use error/(2K) for both response and mass intervals. For sharp_tails n=500, oracle width .026207 (`summary.csv:L175`) versus feasible tails CP .053795 (`L171`) is a comparison of complete procedures, not isolated “cost of estimating masses.” Do not attribute the entire gap to mass uncertainty.
5. **Selection is not free.** SafeCP selects among four candidates built at alpha/4 (`intervals.py:L144–149`), not among ordinary 95% candidates. It need not be narrower than labeled CP. Unsafe selection's good observed coverage (e.g. sharp_tails cell 10, `summary.csv:L174`) does not validate post-selection coverage; no formal guarantee follows from choosing the shortest unadjusted interval.
6. **Respect the declared families.** The two Hoeffding supplements are descriptive and excluded from the locked 180/72/252 families (`multiplicity_manifest.json:L17`). Other paired rows with tiny unadjusted p-values are not automatically confirmatory. Fixed-coefficient PPI's zero rejected tests is not a validity certificate. Pairwise ratio intervals are pointwise even where the test is Holm-adjusted.
7. **Fix tail terminology.** `design_addendum.md:L7` says “upper-tail undercoverage tests”; the manifest (`L16`), saved p-values, and code correctly use the **lower tail of coverage hits** (equivalently upper tail of misses). This is a wording inconsistency, not a computed-test bug.
8. **Document numerical fallbacks separately.** The addendum promises nonfinite fail-safe occurrences are counted (`L6`), but the supplied summaries/raw diagnostic schema do not expose those counts. Endpoint finiteness checks cannot establish that no fail-safe replacement occurred. This is an auditability/reporting gap, not evidence of actual nonfinite failures. Similarly, simulations do not formally certify beta-quantile numerical error.

**Trustworthy claims:** scenario-specific multiplicity-adjusted sharp-tail width gains; empirical conservatism of safeCP in these nonshift cells; severe small-n rare-event Wald undercoverage; real-population width penalties; clipping/shift failure. **Unsupported claims:** exact empirical coverage must exceed nominal; 100% empirical means true coverage=1; safeCP always beats PPI++/labeled CP; asymptotic non-rejection proves validity; general shift robustness; isolated mass-estimation cost; deployment-level generalization from empirical-population resampling.

### Recommended next steps (none executed)

1. Revise claims/tables using the existing paired effects, MC intervals, declared Holm families, and explicit failure labels above; preserve the suspicious rows rather than silently excluding them.
2. Complete an existing-output audit trail for clipping, selector frequencies, and any recorded fallback counts. If untruncated endpoints/fallback flags were never saved, state that limitation rather than reconstructing them as observed data.
3. Only if future experiments are authorized: use a **prespecified matched-response-error-allocation known-mass ablation** to isolate mass-estimation cost. No such experiment is needed or authorized for this audit, and none was run.

## Produced artifacts

- Requested report: `/work/analysis_audit.md`.
- Reproducible, analysis-only script: `/artifacts/analysis_audit_checks.py`.
- Input hashes, formula discrepancies, selected raw diagnostics: `/artifacts/analysis_audit_checks.json`.
- Full declared width family with row locators/effects: `/artifacts/confirmatory_width_audit.csv`.
- All exact-family coverage bounds with locators: `/artifacts/exact_coverage_audit.csv`.
- All asymptotic undercoverage tests with locators: `/artifacts/asymptotic_undercoverage_audit.csv`.
- Per-seed mean widths/ratios: `/artifacts/seed_width_audit.csv`.
- Exploratory analytic labeled-CP check: `/artifacts/analytic_label_cp_diagnostic.csv`.

No figures were needed or produced. Artifact file-tool paths `/artifacts/...` correspond to host `/work/artifacts/...` in this runtime. All seven requested input hashes were unchanged after analysis.
