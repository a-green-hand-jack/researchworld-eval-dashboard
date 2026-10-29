# Global glacier mass change, 2000–2023: an audited observational benchmark and assessment of method dependence

## Abstract

Reconciling glacier observations requires harmonizing temporal support, measurement units, spatial coverage, and shared information across methods. We audit the GlaMBIE version 1.0.0 archive, independently verify its regional-to-global aggregation, deliver complete annual regional and global benchmark tables, and investigate method agreement and error covariance. The supplied archive contains 257 input CSV files and 24,162 observation intervals, rather than a one-to-one representation of the 233 scientific estimates described by the project. The released calendar-year product contains 456 regional and 24 global annual estimates. Its global mass change is **−6,542.5 ± 387.0 Gt** during 2000–2023, equivalent to **−272.6 ± 16.1 Gt yr⁻¹** and a mean specific change of **−0.406 m w.e. yr⁻¹**. These 95% intervals reproduce the publication under independent-error aggregation. Annual mass loss increases by **36.3%** between 2000–2011 and 2012–2023; a ratio interval derived from the released marginal errors is 20.8–54.6%, wider than the publication’s reported percentage interval. All 19 regions lose mass over the full period, and 2023 has the largest estimated annual global loss, 548.0 ± 120.2 Gt. Across 453 released hydrological region-years, 55.6% have only one method group supplying its own annual variability. A simplified, equal-method reconstruction agrees with the released hydrological consensus to 0.0174 m w.e. root-mean-square error, but is a consistency check using shared inputs. Moderate temporal and spatial error correlations increase the uncertainty of the global mean to ±39.7 Gt yr⁻¹. The delivered series is therefore an established consensus benchmark with explicitly conditional uncertainties, rather than a newly independent observation of glacier mass loss.

## 1. Motivation, related work, and research questions

Glacier mass change affects sea level, freshwater supply, and mountain hazards. A useful observational benchmark must resolve both the long-term mass budget and its annual variability. Glaciological measurements provide the latter but sparsely sample glacier populations and do not directly measure frontal ice discharge. DEM differencing provides broad spatial coverage and strong multi-year constraints; altimetry and gravimetry offer complementary temporal information but have distinct spatial sampling and leakage limitations.

Zemp et al. (2019) combined glaciological and geodetic observations to reconstruct mass change over 1961–2016, demonstrating the value of combining annual variability with spatially representative trends. Hugonnet et al. (2021) substantially improved global spatial coverage using satellite elevation differences and estimated a 2000–2019 loss of 267 ± 16 Gt yr⁻¹. The GlaMBIE Team (2025) subsequently reconciled the principal observational methods, explicitly separating their mean rates and annual anomalies and extending coverage through 2023.

This benchmark matters for projection studies. Hock et al. (2019) documented substantial variation among global glacier models; Marzeion et al. (2020) showed that glacier-model uncertainty is particularly important during the first half of the century. Rounce et al. (2023) demonstrated strong sensitivity of future glacier loss to warming using glacier-specific calibration data. These studies motivate regional evaluation with observations whose temporal support, provenance, and uncertainty assumptions are explicit. No model projections are re-estimated in the present analysis.

We test three questions: (1) can the supplied benchmark be reproduced at the aggregation and unit-conversion levels; (2) does availability of multiple methods imply independently supplied annual variability; and (3) how sensitive are cumulative loss and changes in loss rate to plausible error-correlation structures? The working hypothesis is that large-scale mass loss is robust, while precision and apparent annual agreement depend on shared variability and covariance assumptions. These are diagnostic hypotheses, not a formal preregistered confirmatory analysis.

## 2. Data and scope

### 2.1 Archive inventory and quality audit

The primary source is the GlaMBIE dataset, DOI [10.5904/wgms-glambie-2024-07](https://doi.org/10.5904/wgms-glambie-2024-07), version 1.0.0, dated 16 July 2024 in the accompanying metadata. All supplied data and reference PDFs were read without modification. The five provided papers were examined, and the GlaMBIE article and supplementary information were retrieved to resolve methodological details. Downloaded references and extracted text are retained under `outputs/literature/`.

| Archive label | Input CSV files | Role in reconciliation |
| --- | ---: | --- |
| Glaciological | 38 | Annual variability, including seasonal-conversion series |
| DEM differencing | 42 | Spatially representative multi-year rates |
| Altimetry | 41 | Elevation-change rates and available annual variability |
| Gravimetry | 78 | Regional mass change, subject to leakage and confidence screening |
| Hybrid (`combined`) | 58 | Components assigned to appropriate methods by GlaMBIE |
| **Total** | **257** | **24,162 observation intervals; 35 distinct author strings** |

The project describes 233 scientific estimates from 35 research teams and approximately 450 contributors; its article identifies 195 estimates used and 38 excluded by expert evaluation. These counts cannot be equated directly with filenames. Eighteen archive files are explicitly named `GlaciolSineWave`, and variants also occur, for example two Iceland mass-balance products. Excluding those 18 files would leave 239, not 233. The precise file-to-scientific-estimate mapping is not supplied in machine-readable form and is not inferred here. The 35 distinct author strings agree numerically with the reported team count but are not a separate verification of team membership. Counting all 257 files as independent observations would be inappropriate.

The raw archive contains 7,011 rows labeled `mwe`, 1,881 labeled `m`, and 15,270 labeled `Gt` or `gt`. Intervals range from subannual to multi-year support. The audit finds 133 rows with at least one non-finite date, change, or error; 50 negative error entries, all in the two Iceland Pálsson products; and one zero-error entry. No nonpositive-duration intervals or duplicated date intervals within a file were found. Most non-finite rows occur in ten Harig gravimetry files (13 each); three occur in the Russian Arctic Jakob altimetry file. These are archive diagnostics, not evidence that the released consensus propagated these entries uncorrected. We neither take absolute values of signed errors nor silently invent missing raw observations. The file inventory records every issue.

### 2.2 Released products and analysis boundary

The calendar-year directory supplies 24 annual intervals, `[2000,2001)` through `[2023,2024)`, for each of 19 regions and for the globe: **480 records** with mass changes, specific mass changes, glacier areas, and uncertainty half-widths. All required numeric fields are finite, areas and errors are positive, and region–year keys are unique. This product is the primary delivered benchmark.

The hydrological-year directory additionally supplies the reconciled method groups: DEM differencing plus glaciological variability (Dg), altimetry (A), and gravimetry (G). It contains **453 region-years**, not 456: the Southern Andes, New Zealand, and Antarctic/subantarctic regions each have 23 intervals, while the remaining regions have 24. We retain their actual dates and do not fill the missing hydrological end intervals. Northern intervals run approximately October–September, southern intervals April–March, and low-latitude intervals follow calendar years. Method comparisons use identical hydrological intervals within each region; the global series uses calendar years throughout.

This study does **not** claim a complete independent reprocessing of all raw submissions. The supplied files do not encode all expert selections, hybrid assignments, intermediate calibrations, or covariance information needed for that claim. We use the already reconciled release to preserve those scientific decisions, independently verify aggregation, and implement a transparent secondary reconciliation at the homogenized method-group level. This makes the distinction between reproduced results and new diagnostics explicit.

![Archive composition and annual information coverage](images/01_data_overview.png)

**Figure 1. Data overview.** Left: raw CSV counts by region and archive method label; these are not independent sample sizes. Right: number of released method groups supplying their own annual variability, using the metadata flag equal to one. The display label is `floor(start_date + 0.5)` and is only a plotting index; exact hydrological dates are retained in the outputs. White cells indicate no released hydrological interval. Dg counts as one reconciled group. “Own variability” does not establish statistical independence from other groups.

## 3. Methods

### 3.1 Scientific reconciliation inherited from GlaMBIE

The published workflow first homogenizes spatial, temporal, and unit domains, then separates each series into its mean rate and annual anomalies. Glaciological observations constrain variability but not regional mean rates; their anomalies are combined with DEM-derived rates. Altimetry and gravimetry are processed separately. Hybrid contributions are assigned according to which observations constrain their means and anomalies, avoiding their treatment as an additional independent method. Regional groups are then combined with equal method weights, and regional results are seasonally corrected to calendar years before global aggregation (GlaMBIE Team, 2025).

The published density conversion for elevation change uses 850 kg m⁻³, with prescribed density uncertainties increasing for shorter survey intervals. Glacier area varies through time using region-specific area-change rates; a general 5% area uncertainty is used in the source methodology. Gravimetry is excluded from the consensus in regions where its spatial resolution, hydrological leakage, or separation from ice-sheet signals precludes adequate confidence. Seven regions retain gravimetry, whereas 13 have altimetry. Repeating an inverse-variance average of all raw rows would give disproportionate influence to monthly records and duplicate information and would disregard these decisions.

### 3.2 Units, regional aggregation, and temporal summaries

Negative values denote loss. An annual CSV value is an integrated change over a one-year interval; its numerical value also equals the mean rate over that interval. Regional mass changes add directly:

\[
M_t=\sum_{r=1}^{19}M_{rt},\qquad
b_t=\frac{\sum_r A_{rt}b_{rt}}{\sum_r A_{rt}}.
\]

A reproducibility detail is essential: the released files satisfy

\[
M_{rt}\,[\mathrm{Gt}]=0.000997\,A_{rt}\,[\mathrm{km^2}]\,b_{rt}\,[\mathrm{m\ w.e.}].
\]

This corresponds to the software’s water-density constant of **997 kg m⁻³**. The usual definition of metre water equivalent uses 1,000 kg m⁻³, as stated in the article’s prose. The exact factor 0.997 is empirically verified in every regional and global annual record and confirmed in the archived software constants. To avoid a silent 0.3% conversion discrepancy, the principal `specific_change_mwe` field preserves the published numerical convention, while `specific_change_mwe_density1000 = 1000 M/A = 0.997 b` provides the standard-density equivalent. Reported figures and tables use the source convention unless specified otherwise. Gigatonne values are unaffected.

Period means are unweighted means of the annual regional rates. Global specific change is area-weighted within each year and then averaged across years. The sum of specific annual changes is an index over changing glacier area, not a fixed-footprint thickness loss. Sea-level equivalents are descriptive conversions using 362.5 Gt mm⁻¹; they are not measurements of actual ocean response and include mass loss from endorheic basins.

### 3.3 Uncertainty convention and propagation

The result metadata describe “errors” without specifying the confidence level. We resolve this from the article’s stated 95% reporting convention and numerical checks: the global 2023 file gives ±120.16 Gt, matching the published ±120 Gt; quadrature across years gives ±387.02 Gt cumulatively and ±16.13 Gt yr⁻¹ for the mean, matching the publication. The Western Canada altimetry–Dg comparison also reproduces the published rounded ±0.12 m w.e. yr⁻¹. We consequently treat result-file errors as **95% half-widths**, not standard deviations. Gaussian one-sigma equivalents are provided as half-width divided by 1.96. Raw input error conventions are not assumed to be uniform.

For independent regional errors, the annual global half-width is \(H_t=(\sum_r H_{rt}^2)^{1/2}\). For an independent sequence of \(n\) annual errors, the cumulative half-width is \((\sum_t H_t^2)^{1/2}\), and the mean half-width is this quantity divided by \(n\). This reproduces the published benchmark but does not validate independence.

For sensitivity analysis, let \(s_{rt}=H_{rt}/1.96\). We prescribe a separable error correlation model:

\[
\operatorname{Cov}(\epsilon_{rt},\epsilon_{su})
=s_{rt}s_{su}R^{S}_{rs}R^{T}_{tu},\qquad
R^S=(1-c)I+c\mathbf{1}\mathbf{1}^{\mathsf T}.
\]

Temporal scenarios use either \(R^T_{tu}=\rho^{|t-u|}\), with \(\rho=0,0.3,0.6,0.9\), or a persistent shared component \(R^T=(1-q)I+q\mathbf{1}\mathbf{1}^{\mathsf T}\), with \(q=0.10,0.25,1\). Spatial scenarios use \(c=0.10\) or 0.25, including one joint case with \(\rho=0.6,c=0.10\). The persistent parameter is the fraction of standardized error variance shared across years, not a physical climate trend. All scenarios preserve the regional annual marginal errors. Cross-region scenarios deliberately change the global annual error by relaxing the release’s regional-independence assumption.

For any linear summary \(w^{\mathsf T}M\), uncertainty follows \(1.96\sqrt{w^{\mathsf T}\Sigma w}\). The 12-year difference uses weights −1/12 in the first half and +1/12 in the second. The percentage increase in loss is \(100(L_2/L_1-1)\), with positive loss magnitudes \(L_1,L_2\). We provide both first-order delta-method half-widths and Fieller ratio intervals. Fieller intervals solve \((L_2-RL_1)^2\leq1.96^2\operatorname{Var}(L_2-RL_1)\); they accommodate the asymmetry of a ratio with an uncertain denominator. The error models are sensitivity assumptions, not estimates inferred from autocorrelation of the climate signal. Neither these intervals nor the trend diagnostics include all potential structural biases.

### 3.4 Method agreement and simplified reconstruction

Available group values do not necessarily contain independently supplied annual information. A flag of one explicitly identifies a group that provides its own annual variability; all other flag values, including missing flags, are treated as not demonstrating own variability. Pairwise mean differences use all common released intervals. Pearson correlations are calculated only where both groups have a flag of one. We also export correlations over all overlapping values to expose sensitivity to borrowed variability. Correlations are descriptive; no p-values are assigned to small, serially structured, shared-input samples.

The secondary reconstruction is deliberately simple. For each region, let \(C\) be the intersection of dates with values from every available group, and let \(\mu_m\) be group \(m\)’s mean on \(C\). Form annual anomalies \(a_{mt}=b_{mt}-\mu_m\), retaining only own-variability years. Then

\[
\widehat b_t=\frac{1}{|J_t|}\sum_{m\in J_t}a_{mt}
+\frac{1}{K}\sum_{m=1}^K\mu_m,
\]

where \(J_t\) comprises groups with their own variability in year \(t\), and \(K\) is the number of groups in the region. Dg supplies variability throughout all released hydrological intervals. This construction tests the mean–anomaly principle without attempting to reproduce all intermediate calibration periods or gap adjustments. Its output is diagnostic and does not replace the primary calendar-year benchmark or acquire a separately validated uncertainty estimate.

A leave-one-method-out diagnostic recomputes the equal-weight group mean on the **same** common dates. Resulting regional shifts are also expressed as Gt yr⁻¹ using each region’s mean calendar-year area. Summing these equivalents describes potential weighting sensitivity over the supported regions; differing regional comparison periods prevent interpreting that sum as a newly reconstructed global annual time series. Regions with only one method group do not support this diagnostic.

### 3.5 Validation design

Validation has three levels: arithmetic/unit closure, consistency of the simplified reconstruction, and matched-period comparison with published estimates. None constitutes independent field validation. The Hugonnet dataset contributes to GlaMBIE, and the released method groups also contribute to the consensus. We compare Hugonnet et al. over calendar years 2000–2019. Zemp et al.’s reported 2006–2016 estimate represents ten hydrological years, 2006/07–2015/16, and is discussed as context rather than being incorrectly matched to eleven calendar years. We do not use withheld observations because no independent regional reference series is supplied.

## 4. Results

### 4.1 Global annual and cumulative mass change

The independent sum of 19 regional annual mass changes agrees with the released global series to a maximum absolute residual of **1.14 × 10⁻¹³ Gt**. Annual global error quadrature agrees to **2.84 × 10⁻¹⁴ Gt**. Area-weighted specific changes and their regional-error aggregation also close numerically. The 997 kg m⁻³ unit relation closes to **5.68 × 10⁻¹⁴ Gt**.

Over the 24 calendar years, the benchmark gives **−272.60 ± 16.13 Gt yr⁻¹** and **−6,542.47 ± 387.02 Gt** cumulatively, using independent-error propagation. The mean specific rate is **−0.40595 m w.e. yr⁻¹** under the source convention, or **−0.40473 m w.e. yr⁻¹** at 1,000 kg m⁻³. The summed specific-change index is −9.743 m w.e. The equivalent sea-level contribution is **18.05 ± 1.07 mm**, or **0.752 ± 0.044 mm yr⁻¹**.

The first-half mean is **−230.72 ± 23.05 Gt yr⁻¹**, and the second-half mean is **−314.48 ± 22.55 Gt yr⁻¹**. Thus the later period loses **83.76 ± 32.25 Gt yr⁻¹** more mass, a 36.30% increase in magnitude. Under independent annual errors, the first-order percentage half-width is 16.76 percentage points and the Fieller 95% interval is **20.77–54.58%**. The article reports 36 ± 10%; that particular uncertainty is **not reproduced by standard ratio propagation from the released annual marginal errors**. Additional covariance or a different propagation rule would be required to recover it; we do not invent one.

The largest point estimate of annual loss is **548.03 ± 120.16 Gt in 2023**, with specific change **−0.843 ± 0.166 m w.e.** Its interval overlaps that of 2022 (−460.30 ± 100.83 Gt), so “largest estimated loss” should not be read as a statistically established difference from the preceding year. The last two years account for 15.4% of cumulative loss, and 2019–2023 accounts for 31.2%.

The descriptive linear slope of annual mass change is −9.98 Gt yr⁻² over 2000–2023, compared with −6.63 Gt yr⁻² when 2022–2023 are omitted. The slope remains negative over all tested start/end windows but is strongly endpoint-dependent. This is a descriptive summary of the observational series, not an attribution analysis or evidence of constant future acceleration.

![Global annual and cumulative glacier mass change](images/02_global_mass_change.png)

**Figure 2. Global mass change.** (a) Calendar-year values with released 95% intervals and equal-length period means. (b) Cumulative change from the start of 2000 through the end of 2023, with 95% bands under independent, temporally correlated, and combined temporal/spatial error scenarios. Scenario bands quantify measurement-error assumptions; they are not alternative mass trajectories.

### 4.2 Regional distribution

Every region has negative mean mass change during 2000–2023. Alaska contributes **22.53%** of the global loss; Arctic Canada North and South together contribute **19.60%**; Greenland periphery contributes **13.00%**; and the Southern Andes contributes **9.64%**. These five regional units account for approximately 64.8% of total loss. The most negative mean specific rates occur in Central Europe (−1.062 m w.e. yr⁻¹), New Zealand (−0.961), and the Southern Andes (−0.919). Consequently, the largest total contributors are not necessarily the regions with the most intense loss per unit area.

Mass-loss magnitude increases between the two halves in **13 of 19 regions when measured in Gt yr⁻¹**, and **14 of 19 in m w.e. yr⁻¹**. Greenland periphery illustrates why the distinction matters: its specific loss becomes more negative, while its total annual loss becomes slightly less negative as the assigned glacier area decreases. Arctic Canada North, Arctic Canada South, Iceland, Scandinavia, and the low latitudes have less negative specific mean rates in the second half. These descriptive sign comparisons are not separate significance tests across 19 regions.

**Table 1. Calendar-year regional summaries, 2000–2023.** Uncertainties on the means are 95% half-widths under independent annual errors. A negative value in the last column indicates increased mass loss. Specific changes retain the source density convention. The table uses calendar years consistently and can therefore differ from published regional tables summarized on hydrological years.

{{REGION_TABLE}}

![Regional annual patterns and mass-loss contributions](images/03_regional_patterns.png)

**Figure 3. Regional pattern and contribution.** (a) Annual specific changes, emphasizing differences in loss intensity; the most negative cell extends below the displayed color scale. (b) Average annual total loss with independence-based 95% intervals, emphasizing regional contributions to the global budget. Regions are ordered by contribution in panel b.

![Regional time series with annual uncertainty](images/04_regional_annual_uncertainty.png)

**Figure 4. Complete regional annual benchmark.** Specific mass changes and released 95% intervals for all 19 regions. Vertical scales vary by region to preserve annual detail. Wider endpoint intervals and large uncertainties in some polar regions are part of the supplied product, not imputed precision.

### 4.3 Annual information and method dependence

Dg has values and own variability in all 453 hydrological region-years. Altimetry has 213 available estimates but only **124 own-variability flags**, and gravimetry has 140 estimates with **126 own-variability flags**. Thus 89 altimetry and 14 gravimetry values do not demonstrate their own annual variability. In **252 of 453 region-years (55.6%)**, only one group supplies its own annual variability; two groups do so in 152 cases and three in only 49 cases (10.8%). Annual output completeness therefore exceeds the extent of direct annual corroboration by several methods.

On overlapping periods, altimetry is on average **0.081 m w.e. yr⁻¹ less negative than Dg**, averaged equally across its 13 regions. Gravimetry is **0.011 m w.e. yr⁻¹ less negative**, averaged across its seven retained regions. These means use region-specific overlap periods and are not global area-weighted biases. Western Canada/USA exhibits an altimetry–Dg difference of **+0.195 ± 0.125 m w.e. yr⁻¹**. Gravimetry differs from Dg by **+0.211 ± 0.065** in Alaska and **−0.229 ± 0.239 m w.e. yr⁻¹** in the Southern Andes. Pairwise intervals here assume independence across methods and years; shared observations make them conditional diagnostics.

The apparent agreement of annual fluctuations changes markedly when borrowed variability is excluded. For South Asia West, the altimetry–Dg correlation is **0.822 over 21 overlapping years**, but **−0.452 over the seven years where both groups supply their own variability**. Corresponding values in Central Asia are 0.456 and −0.576. These are different temporal samples as well as different availability filters, so the change cannot be attributed entirely to borrowing. Nevertheless, it demonstrates why the full interpolated or calibrated series is not valid evidence of independent annual corroboration. Small samples, shared data, differing sensors, and genuine interannual sampling differences preclude interpreting the negative correlations as proof that one method is incorrect.

The simplified equal-method reconstruction has **0.0174 m w.e. RMSE** across all 453 intervals and **0.0210 m w.e. RMSE** in regions with more than one group. Its largest absolute residual is 0.126 m w.e.; the largest regional RMSE occurs in the Antarctic/subantarctic region (0.0525 m w.e.). Single-group regions are reproduced almost exactly by construction and are not evidence of successful independent validation. Residuals in multiple-group regions reflect the intentionally simplified common-period treatment relative to the full workflow.

Removing altimetry from the common-period means shifts the sum of area-equivalent regional rates by **−23.29 Gt yr⁻¹** across supported regions. Removing Dg shifts it by **+22.79 Gt yr⁻¹**, and removing gravimetry by **+0.50 Gt yr⁻¹**. The small gravimetry sum reflects cancellation of regional shifts, not negligible regional influence. These diagnostics show that method weighting can matter at a scale comparable to the published global mean uncertainty. They are not new global time series, because common periods differ among regions and unsupported regions cannot undergo a method-removal test.

![Method differences and annual variability agreement](images/05_method_comparison.png)

**Figure 5. Method comparison on matched hydrological intervals.** Left and center: mean differences from Dg with 95% half-widths assuming independent errors. Positive differences mean less negative estimates. Right: correlations with Dg restricted to intervals where both groups supply their own variability; point labels are the region IDs in Table 1. Comparisons have unequal sample sizes and no claim of independent truth.

### 4.4 Consistency with published assessments

The 2000–2023 benchmark reproduces the GlaMBIE article’s rounded mean, cumulative loss, and 2023 extreme. Over **2000–2019**, the benchmark is **−245.57 ± 16.79 Gt yr⁻¹**, compared with **−267 ± 16 Gt yr⁻¹** in Hugonnet et al. (2021). This is **21.43 Gt yr⁻¹, or 8.03%, less negative**, matching the direction and scale of the GlaMBIE paper’s comparison. The reported intervals overlap. Because Hugonnet observations are included in GlaMBIE, the two estimates are correlated and this comparison is not an independent test of accuracy or uncertainty coverage.

Zemp et al. (2019) reported −335 ± 144 Gt yr⁻¹ for the hydrological decade 2006/07–2015/16, illustrating the wider uncertainty of an earlier global extrapolation. That value is not plotted against an unmatched calendar-year interval. Likewise, this study does not recreate IPCC tables from secondary descriptions or compare model scenarios without the corresponding model data.

![Aggregation checks, simplified reconstruction, and literature comparison](images/06_validation.png)

**Figure 6. Validation and comparison.** (a) Independent regional aggregation reproduces annual global mass changes and uncertainty quadrature to floating-point precision. (b) Simplified hydrological reconciliation compared with the release; single-group agreement is built into the method. (c) Published global estimates and the benchmark over exactly matched calendar periods. The GlaMBIE comparison is a reproduction check, and the Hugonnet comparison involves overlapping input information. Error bars are 95% intervals under each source’s stated assumptions.

### 4.5 Sensitivity to error correlations

The mean mass-loss estimate remains **272.6 Gt yr⁻¹** in every covariance scenario; only uncertainty changes. An annual AR(1) error correlation of 0.6 increases the 95% half-width of the mean from **16.1 to 30.0 Gt yr⁻¹**. Adding a common cross-region correlation of 0.10 increases it to **39.7 Gt yr⁻¹**, with cumulative uncertainty **±951.7 Gt**. A persistent component with \(q=0.25\) produces **±41.1 Gt yr⁻¹**, about 2.55 times the independence result.

Mean loss and changes in loss rate respond differently to correlation. A persistent common error is not averaged away in a long-term mean, but can largely cancel in a difference between equal-length periods. By contrast, moderate temporal persistence increases the uncertainty of the period difference. In the joint \(\rho=0.6,c=0.10\) case, the later-period increase in loss is **83.8 ± 73.7 Gt yr⁻¹**: positive at the nominal 95% level under that particular model, but much less precisely resolved. All tested Fieller intervals also remain above zero. This is robustness within the specified covariance scenarios, not a bound on all possible systematic biases.

**Table 2. Covariance sensitivity.** All scenarios retain the same observed mean and 36.3% point estimate of increased loss. Widths are conditional 95% quantities; parameters are illustrative assumptions, not fitted values.

{{COVARIANCE_TABLE}}

![Covariance sensitivity of mean loss and increased loss rate](images/07_covariance_sensitivity.png)

**Figure 7. Correlation affects different estimands differently.** (a) Half-width of the 24-year mean. (b) Increase in loss magnitude from 2000–2011 to 2012–2023, with conditional 95% intervals. Persistent shared errors broaden mean uncertainty but may cancel in differences; temporally evolving and cross-region correlations can weaken precision on the difference.

## 5. Discussion and implications for model calibration

The archive supports a coherent, globally complete annual benchmark. Arithmetic closure, matched-period reproduction, and the secondary reconciliation show that its published large-scale structure is recoverable. The spatial pattern separates two concerns: large glacierized regions dominate the global sea-level-equivalent budget, whereas small mountain regions can undergo more intense loss per unit area. Calibration should therefore evaluate both total and specific changes instead of optimizing only global mass loss.

Our new diagnostics identify a distinction between **annual resolution** and **independent annual information**. More than half of released hydrological region-years derive annual variability from one group. Satellite methods can still strengthen the mean-rate constraint in those years, but should not automatically be counted as additional annual validation. Correlations involving gap-filled or borrowed anomalies are especially liable to overstate corroboration. Even a flag of one does not remove shared sensors, geodetic baselines, or regional proxy dependence; for example, the source methodology substitutes nearby glaciological series where observations are absent.

The covariance sensitivity demonstrates why ±16 Gt yr⁻¹ is a conditional precision statement rather than an exhaustive uncertainty bound. Data from common sensors, shared density conversions, glacier outlines, and calibrated means can create error dependence across years and regions. The marginal errors alone do not identify these dependencies. We have not estimated a “best” correlation or replaced the source intervals with a calibrated posterior. Instead, the delivered covariance scenarios make the consequences visible and reproducible. The unreproduced ±10% uncertainty on the published relative increase further illustrates the need to distribute explicit covariance and aggregation rules alongside point estimates.

For climate-model evaluation, the benchmark should be used with its exact calendar bounds, changing-area convention, and sea-level-relevant glacier scope. The Greenland and Antarctic ice sheets are excluded; their peripheral glacier regions are included. The original assessment emphasizes mass change relevant to sea level and does not fully represent below-water or frontal-retreat volume changes in every setting. A model of total glacier ice volume must therefore use a compatible definition before scoring residuals. Regional hydrological outputs are useful for seasonal model diagnostics but should not be summed as if all dates were synchronous calendar years.

Annual errors should not simply be treated as independent regression weights without a sensitivity check. Users can evaluate model residuals under the provided global covariance matrices or construct the documented regional covariance model from annual marginal errors. A multi-year mean and a set of annual anomalies offer complementary constraints. Independent validation requires observations excluded from calibration, preferably high-quality glacier-scale measurements propagated to regional support. Comparisons with Hugonnet or the released method groups cannot supply that independence because of shared inputs. These recommendations directly address the calibration and initialization sensitivities documented by Hock et al. (2019), Marzeion et al. (2020), and Rounce et al. (2023).

## 6. Limitations

The primary estimates and marginal uncertainties are inherited from the GlaMBIE consensus. This report adds an audit, transparent exports, method-level consistency checks, and covariance sensitivity; it does not introduce a new independent global observation. The unexplained remainder of the 257-file versus 233-estimate accounting prevents a definitive raw-file inclusion ledger. Raw negative and missing error entries require source-specific interpretation before any full reprocessing.

Method groups share information, pairwise overlaps vary, and annual flags identify provenance rather than statistical independence. The simplified reconstruction omits some calibration and seasonal-correction steps and is evaluated against a consensus constructed from the same groups. Its low RMSE is consequently an internal consistency result. There is no empirical coverage validation of the released error bars.

Error-correlation parameters are hypothetical. Gaussian approximations, linear summary propagation, and Fieller intervals do not account for all non-Gaussian errors, density-conversion biases, structural errors in glacier area, or undocumented expert choices. Correlation of actual glacier changes is not an estimate of measurement-error correlation. The observed increase in loss does not identify its climatic causes, and the endpoint-sensitive linear slope should not be extrapolated. Sea-level equivalents do not substitute for ocean-budget attribution, and annual regional data do not resolve seasonal runoff or local hazard changes.

## 7. Conclusion

The delivered annual benchmark covers every calendar year from 2000 through 2023 for 19 glacier regions and the globe, with mass changes and uncertainties in Gt and m w.e. It reproduces the published cumulative loss of approximately **6.54 trillion tonnes** and the **36.3%** increase in annual loss between the two halves of the record. All regions lose mass over the full period. The audit shows that the precision of long-term summaries and apparent agreement of annual variability depend on information sharing and covariance assumptions. Preserving those distinctions makes the consensus more useful as an observational reference for assessment reports and model calibration without claiming an independently validated uncertainty bound.

## 8. Reproducibility and deliverables

The analysis is deterministic. `code/analyze.py` reads the immutable input archive, checks its numerical consistency, builds the analysis tables, and creates all seven PNG figures. `code/build_report.py` renders this report using computed tables and `code/report_template.md`. `code/validate_outputs.py` checks deliverable completeness, source fidelity, numerical aggregation, covariance matrices, and report image links. `code/requirements.lock.txt` records the installed package versions. A complete rerun from `/work` is:

```bash
/work/.venv/bin/python /work/code/analyze.py
/work/.venv/bin/python /work/code/build_report.py
/work/.venv/bin/python /work/code/validate_outputs.py
```

A fresh environment can be created from the instructions in `code/README.md`. Internet access is unnecessary for rerunning the numerical analysis. Reference downloads are archived separately and are not executable dependencies. The code preserves the input files, and `outputs/input_checksums.csv` records their SHA-256 hashes.

| Deliverable | Contents |
| --- | --- |
| `outputs/annual_mass_change_2000_2023.csv` | All 480 annual records; explicit 95% and one-sigma errors, source and standard-density specific-change fields |
| `outputs/regional_annual_2000_2023.csv` | 456 regional annual records |
| `outputs/global_annual_2000_2023.csv` | 24 global annual records |
| `outputs/cumulative_mass_change.csv` | Regional/global cumulative changes and independence-based uncertainties |
| `outputs/regional_period_summary.csv` | Full-period rates, totals, loss shares, and half-period comparisons |
| `outputs/input_inventory.csv` | Every raw file, metadata, interval properties, and quality flags |
| `outputs/method_series_hydrological.csv` | Released method-group results, with original dates and flags |
| `outputs/method_availability.csv` | Method presence distinguished from own annual variability |
| `outputs/method_pair_comparisons.csv` | Matched-period offsets, correlations, and sample counts |
| `outputs/simplified_reconciliation_hydrological.csv` | Diagnostic reconstruction and residuals |
| `outputs/leave_one_method_out.csv` | Common-period method-weighting sensitivity |
| `outputs/covariance_sensitivity.csv` | Explicit uncertainty scenarios, differences, and ratio intervals |
| `outputs/global_covariance_scenarios.npz` | Global 24 × 24 covariance matrices in Gt², using one-sigma scaling; years 2000–2023 in order |
| `outputs/literature_comparisons.csv` | Exactly matched calendar-period comparisons |
| `outputs/aggregation_checks.csv` | Numerical closure residuals |
| `outputs/README.md` | Field definitions, conventions, and interpretation boundaries |
| `report/images/` | Seven PNG figures referenced in this report |

## Appendix A. Annual global benchmark

Each year labels `[year, year + 1)`. Uncertainties are the released annual 95% half-widths; they are not temporal standard deviations. Specific changes retain the source’s 997 kg m⁻³ conversion convention. Machine-readable exports include the 1,000 kg m⁻³ equivalent and all regional values.

{{GLOBAL_ANNUAL_TABLE}}

## References

1. **GlaMBIE (2024).** *Glacier Mass Balance Intercomparison Exercise (GlaMBIE) Dataset 1.0.0.* World Glacier Monitoring Service, Zurich. [doi:10.5904/wgms-glambie-2024-07](https://doi.org/10.5904/wgms-glambie-2024-07). Primary archive and metadata supplied in `data/glambie/`.
2. **The GlaMBIE Team (2025).** Community estimate of global glacier mass changes from 2000 to 2023. *Nature*, **639**, 382–388. [doi:10.1038/s41586-024-08545-z](https://doi.org/10.1038/s41586-024-08545-z). Main article and supplementary information archived in `outputs/literature/`; source for reconciliation, confidence conventions, and expert selections.
3. **Zemp, M., et al. (2019).** Global glacier mass changes and their contributions to sea-level rise from 1961 to 2016. *Nature*, **568**, 382–386. [doi:10.1038/s41586-019-1071-0](https://doi.org/10.1038/s41586-019-1071-0). Supplied as `related_work/paper_002.pdf`.
4. **Hugonnet, R., et al. (2021).** Accelerated global glacier mass loss in the early twenty-first century. *Nature*, **592**, 726–731. [doi:10.1038/s41586-021-03436-z](https://doi.org/10.1038/s41586-021-03436-z). Supplied as `related_work/paper_004.pdf`.
5. **Hock, R., et al. (2019).** GlacierMIP—A model intercomparison of global-scale glacier mass-balance models and projections. *Journal of Glaciology*, **65**, 453–467. [doi:10.1017/jog.2019.22](https://doi.org/10.1017/jog.2019.22). Supplied as `related_work/paper_003.pdf`.
6. **Marzeion, B., et al. (2020).** Partitioning the uncertainty of ensemble projections of global glacier mass change. *Earth’s Future*, **8**, e2019EF001470. [doi:10.1029/2019EF001470](https://doi.org/10.1029/2019EF001470). Supplied as `related_work/paper_001.pdf`.
7. **Rounce, D. R., et al. (2023).** Global glacier change in the 21st century: Every increase in temperature matters. *Science*, **379**, 78–83. [doi:10.1126/science.abo1324](https://doi.org/10.1126/science.abo1324). Supplied as `related_work/paper_000.pdf`.
8. **GlaMBIE software.** Implementation referenced by the GlaMBIE article, archived at [doi:10.5281/zenodo.14186227](https://doi.org/10.5281/zenodo.14186227); [GitHub repository](https://github.com/earthwave/glambie). The downloaded constants file is retained as supporting evidence for the 997 kg m⁻³ water-density convention; the numerical conversion is independently checked against the released data.
