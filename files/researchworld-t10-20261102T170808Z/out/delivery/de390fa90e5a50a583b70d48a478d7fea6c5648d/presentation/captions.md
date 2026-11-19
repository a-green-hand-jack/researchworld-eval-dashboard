# Captions and artifact map

Use figures `main_comparison.pdf` and `finite_comparison.pdf` as the two main full-width displays. `main_results.tex` is an optional compact main table; all other panels/tables support the appendix. All outputs use the 5.5-inch NeurIPS text width. Figure captions go below and table captions above. Captions below are supplied presentation content; the report owner integrates numbering and cross-references.

## Shared statistical conventions

The estimand is the population mean mu=E[Y]. Every method receives identical labeled pairs and frozen unlabeled scores within each independent draw. Confidence intervals for mu target 95% coverage. All displayed coverage error bars are two-sided 95% Wilson **Monte Carlo** intervals for estimated repeated-sampling coverage; they are not confidence intervals for mu. All width ratios are ratios of paired mean widths, with paired delta-method 95% Monte Carlo intervals; errors may be smaller than markers. A width ratio below 1 denotes shortening against the named baseline. Target/reference lines are .95 and 1. No point or Monte Carlo interval near .95 proves finite-sample validity. Results are unfiltered, including poor coverage and unstable large widths.

## Main displays

### figures/main_comparison.pdf

**Caption:** Nonlinear gain, no-gain controls, archived-data results, and a small-sample failure. Points compare scalar PPI++ (ppi-python 0.2.3), an unrestricted scalar control, and a cross-fitted cubic score control on identical inputs. All rows use n=2000 labeled and N=20000 unlabeled observations, except rare Bernoulli (n=100,N=1000); R=5000 independent repetitions per row. Left: coverage with 95% Wilson Monte Carlo intervals. Right: paired ratios of mean widths to PPI++, with 95% delta-method Monte Carlo intervals. The quadratic case shortens substantially; the affine/no-signal and three archived-score cases show negligible additional gain. Rare-event Wald coverage is far below nominal, so its short intervals are failures. Galaxies, forest and AlphaFold are independent with-replacement draws from the archived record lists, targeting each archive's empirical mean; they do not establish natural-population coverage. The scalar and cubic intervals have asymptotic justification, not finite-sample guarantees.

### figures/finite_comparison.pdf

**Caption:** Finite-sample guarantees can coexist with gains or substantial conservatism. All EB methods have bounded-data concentration guarantees under the stated independent iid sampling model; trained scalar/cubic controls reserve training labels from the original n-label budget, while EB label and fixed-PPI baselines use all n. Clopper--Pearson (CP) is an exact binary label-only comparator and is absent for the nonbinary bounded-quadratic rows. All rows use n=2000,N=20000 except the explicitly labeled n=10000 bounded row (N=100000) and n=100 rare-event row (N=1000). Bounded-quadratic rows have R=3000; all binary rows have R=5000. Left: empirical coverage with 95% Wilson Monte Carlo intervals, distinct from theorem guarantees. Right: paired ratios of mean widths to EB label-only with 95% delta-method Monte Carlo intervals. Cubic EB gains in the designed high-signal bounded setting, especially at n=10000; on the archived empirical populations it is wider than label EB, full-label fixed-PPI EB, scalar EB and CP. Archive draws are independent with replacement and target archive means. This compares the specified EB/CP family, not all valid intervals.

### tables/main_results.tex

**Caption:** Large-label main-grid comparisons at n=2000,N=20000,R=5000 for mu=E[Y]. Coverage entries include two-sided 95% Wilson Monte Carlo intervals. The final column is cross-fit cubic mean width divided by PPI++ mean width, plus/minus 1.96 paired delta-method Monte Carlo standard errors. Absolute widths and their Monte Carlo standard errors are in the complete appendix tables. All methods receive the same inputs per draw; archived-data rows target with-replacement empirical populations. Narrowing with undercoverage is not a valid-interval improvement, and coverage compatibility does not prove validity.

## Appendix figures

### figures/synthetic.pdf

**Caption:** Dependence on labeled sample size in quadratic, sigmoid, affine and no-signal synthetic populations. N=10n and R=5000 per setting. Coverage and paired mean-width ratios to PPI++ carry the Monte Carlo intervals defined above. The unrestricted scalar and cross-fit linear controls distinguish nonlinear score information from scalar clipping and fitting cost. Axes vary across rows to expose both large gains and small costs; every error-bar endpoint is retained. Horizontal offsets only separate overlapping methods. These are asymptotically justified Wald intervals.

### figures/real.pdf

**Caption:** The three supplied fixed-score archives show small-label fitting costs and negligible large-label nonlinear gain. Labeled/unlabeled indices are independently sampled with replacement from each archived record list, with its empirical mean used as evaluation truth; no broader scientific-population inference is claimed. N=10n, R=5000 per setting; methods share each draw. Coverage uses 95% Wilson Monte Carlo intervals; mean-width ratios to PPI++ use paired delta-method 95% Monte Carlo intervals. Widths retain all large unstable fits, rather than replacing their means by medians. These Wald intervals have asymptotic, not exact finite-sample, justification.

### figures/stress.pdf

**Caption:** Heavy tails, nonlinear binary outcomes, rare events and a fixed degree-12 cross-fit diagnostic expose finite-sample limitations. N=10n,R=5000 per setting. Coverage uncertainty is 95% Wilson Monte Carlo; paired mean-width-ratio uncertainty against PPI++ is 95% delta-method Monte Carlo. Cross-fitting does not ensure finite-sample validity or stable fitting, and short rare-event Wald intervals fail. The quadratic-Bernoulli width panel uses a logarithmic vertical axis; other panels use linear scales. Axis ranges vary to retain all uncertainty endpoints. All trial outcomes remain in the means.

### figures/finite.pdf

**Caption:** Sample-size dependence of the bounded high-signal quadratic EB comparison. N=10n,R=3000 per setting. Methods and known-range assumptions are those in the finite-sample construction; all training consumes the original n labels. Coverage uses Wilson 95% Monte Carlo intervals and width ratios to EB label-only use paired delta-method 95% Monte Carlo intervals. At n=2000 range penalties almost erase the gain; at n=10000 cubic EB is shorter, while still conservative. The >=95% coverage guarantee follows from assumptions and concentration, independently of these hit counts.

### figures/finite_n.pdf

**Caption:** Finite unlabeled information limits the available gain. Cross-fit cubic results at n=2000 compare N/n=1 (R=3000, a declared follow-up) with N/n=10 (R=5000, original main grid). Left: coverage with 95% Wilson Monte Carlo intervals. Right: measured paired cubic/PPI++ mean-width ratios with 95% delta-method Monte Carlo intervals; dashed lines are the analytical oracle/unrestricted-scalar ratios, not fitted empirical trends. The linear and no-signal oracle curves coincide at 1. The quadratic ratios agree closely with the calculable oracle limit. This is a class-restricted asymptotic comparison, not a universal interval-length bound. Points share identical inputs across methods within each setting; settings are independent repeated-sampling experiments.

## Appendix tables

### tables/finite_results.tex

**Caption:** Bounded-quadratic finite-sample comparison at N=10n,R=3000. Coverage includes 95% Wilson Monte Carlo intervals. Width is its absolute mean in outcome units, with its Monte Carlo standard error in parentheses; it is not itself an uncertainty interval. The final column divides mean width by EB label-only and reports plus/minus 1.96 paired delta-method Monte Carlo standard errors. Training consumes the same original label budget; fixed-PPI and label-only baselines use all n. Guarantees rely on the known bounds and iid sampling, not observed coverage.

### tables/binary_results.tex

**Caption:** Exact label-only CP and bounded EB comparisons at N=10n,R=5000. All five main binary regimes are shown at n=2000, plus the rare-event n=100 failure setting. Coverage includes 95% Wilson Monte Carlo intervals. Absolute mean widths have Monte Carlo standard errors in parentheses. CP denotes Clopper--Pearson, valid for binary iid labels. No fitted EB real-data gain is claimed. The three archive rows target empirical populations under independent with-replacement draws.

### tables/fit_tails.tex

**Caption:** Selected fitting diagnostics at n=100,N=1000,R=5000 for every displayed regime/method. Width medians, empirical 99th percentiles and maxima come directly from saved draw-level results. CF denotes cross-fitting. Extremely large fits remain in all means and uncertainty estimates; high-degree cross-fitting is a stress diagnostic, not an automatically valid alternative. Absolute widths are in outcome units and must not be compared across unrelated populations as if they had a common scale. Archive populations use the sampling law stated above.

### tables/method_assumptions.tex

**Caption:** Coverage scope and additional conditions for the implemented families, checked against analysis/proofs.md and the report owner's supplied content. Independent iid draws from a common population underpin the score-control comparisons; CP uses only iid binary labels. Cross-fitting alone is not finite-sample validity. EB additionally requires the stated support ranges and concentration allocation, with learned controls independent of evaluation labels conditional on training. Scope is not inferred from nonsignificant simulation diagnostics.

### tables/oracle_ratios.tex

**Caption:** Analytical leading-order width ratios in the deterministic score-control class. The oracle uses h*(S)=E[Y|S]/(1+n/N); the scalar comparator uses the population-optimal unrestricted coefficient of S. Entries are square roots of exact variance ratios from analysis code/theory.py, rounded to three decimals. They are theoretical predictions, not measured widths or finite-sample coverage guarantees. The statements are restricted to this estimator class and the specified generators.

### tables/full_results.tex

This self-captioned sequence contains **all 405 method/setting cells**, including every diagnostic method and the n=N follow-up. n,N,R are printed on every row. Coverage includes 95% Wilson Monte Carlo intervals; width is its absolute mean, with MCSE in a separate column. No rows are silently filtered or ranked. Regime headings repeat across page breaks. CF denotes cross-fitting; CP denotes Clopper--Pearson; split and full-label PPI EB are distinct. The source files and full paired comparisons remain machine-readable in tables/all_cells.csv and tables/all_paired.csv.

## Exact source-to-output mapping

Every artifact below is generated by **presentation/render.py**; the analysis source revision and SHA-256 hashes are in presentation/render_manifest.json. Source snapshots under presentation/source/ are byte-identical copies of the named analysis results at that revision.

| Output | Inputs under results/ | Generator function |
|---|---|---|
| main_comparison.pdf, .png | summary.csv, paired.csv | main_comparison -> forest |
| finite_comparison.pdf, .png | summary.csv, paired.csv | finite_comparison -> forest |
| synthetic.pdf, .png | summary.csv, paired.csv (N=10n) | grid |
| real.pdf, .png | summary.csv, paired.csv (N=10n) | grid |
| stress.pdf, .png | summary.csv, paired.csv (N=10n) | grid |
| finite.pdf, .png | summary.csv, paired.csv | grid |
| finite_n.pdf, .png | summary.csv, paired.csv, theory.csv | finite_n |
| main_results.tex | summary.csv, paired.csv | main_table |
| finite_results.tex | summary.csv, paired.csv | finite_table |
| binary_results.tex | summary.csv | binary_table |
| fit_tails.tex | tail_diagnostics.csv | tail_table |
| method_assumptions.tex | verified analysis/proofs.md and supplied report content | assumptions_table |
| oracle_ratios.tex | theory.csv | theory_table |
| full_results.tex | summary.csv | full_table |
| all_cells.csv, all_paired.csv | summary.csv, paired.csv | lossless data export in main |

coverage_diagnostics.csv is retained as a provenance/diagnostic input; plotted coverage is taken from summary.csv, without turning tests into a validity certificate. All file paths are relative to the delivered paper root. No prohibited literature was accessed during presentation work.
