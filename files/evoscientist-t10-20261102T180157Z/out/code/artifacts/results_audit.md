# Results audit: fixed-budget confidence-interval study

## Scope and executive conclusions

Output-only audit dated 2026-11-02. Read the frozen plan/amendment, `results/config.json`, `summary.csv`, `oracle.csv`, and **only** the 32 main `results/raw/*.csv.gz` files. Inspected the existing runner for sampling/provenance, checked frozen hashes, and checked the two empirical data arrays for truth and hashes. No CI method was implemented, imported or rerun; no code agent, web access, supplemental comparator, supplemental configuration, supplemental logs or partial supplemental results were used.

- **Complete and internally consistent:** 32 cells × 2,000 repetitions = 64,000 paired experiment repetitions; 410 method-cells and 820,000 intervals. All expected files/methods/replicate indices exist; zero invalid endpoints and zero coverage-flag disagreements.
- **Undercoverage is real in many finite-n cells:** Holm detects 59/256 asymptotic-tier method-cells (including 10 negative-control cells), 6/26 oracle cells, and 0/128 finite-guarantee cells. The absence of a rejection is **not** evidence proving nominal validity.
- **Nonlinear savings are synthetic and conditional, not uniform:** `cf_rich` at quadratic/n=2000 has width ratio 0.820287213092; step/n=2000 has ratio 0.607022718955, but coverage 0.9355 (Wilson [0.923877579, 0.945452673]). The latter is an unadjusted undercoverage warning, **not** a rejection after the requested tier-wide Holm adjustment (p=4.6938013661e-1).
- **No nonlinear width gains on either empirical distribution:** `cf_rich` is wider than unrestricted `ppipp` in all six empirical cells; its ratios range 1.00356327233–1.36144436711. `cf_poly2` also has point ratios ≥1 in all six; this does not say scalar PPI fails to improve on labeled-only inference.
- **EB is strongly conservative and inefficient relative to CP here:** EB-PPI and EB-selection cover all 2,000 repetitions in every cell. EB-selection is wider than CP in all 32 cells, and improves on standalone labeled EB only in step/n=2000 (ratio 0.941444683741). These are observations, not universal dominance statements.

## 1. Frozen design and completeness

The pre-run amendment supersedes the initial plan: rich basis p=4 (not p=7), epsilon_n=1e-4/n, value-independent index-mod5 folds, corrected fold/unlabeled covariance recipe, stronger step and quadratic mechanisms, clipping to [0,1], and expanded n grid. All 21 core cells and 11 stress cells in config are present, including n=2000, n=30, and the planned N/n∈{1,100} stress cells. No planned amended cell was dropped. There are 26 synthetic cells with 13 methods each and six empirical cells with 12 methods each; oracle is unavailable on empirical data by design, not an incomplete run.

All CSV reads used **`keep_default_na=False`**, preserving the legitimate `null` scenario. There are four `null` cells and no missing-scenario imputation. Within each cell every method has exactly the sorted and saved sequence rep=0,…,1999; there are no duplicate `(method,rep)` keys, no method omissions, and no metadata/truth inconsistencies. Summary has 410 distinct matching keys. The cell-level checks are in `results_audit_cells.csv`.

**Pairing verification boundary:** saved replicate indices align exactly across all methods. The frozen runner constructs one labeled/unlabeled sample per replicate and passes the same arrays into one `all_intervals` call. Seed recipe is `SeedSequence([20261102, sid, n, ratio])`, with sid determined by `['linear','quadratic','step','null','rare','galaxies','forest']`; the 32 tuples are distinct and independent of worker scheduling. However, **raw output contains no labeled/unlabeled sampled-row indices, RNG states, or per-replicate sample hashes**. Thus output-index alignment is verified; underlying sampled-row alignment is supported by source inspection but cannot be independently certified from saved numeric outputs alone. No replay was performed.

Empirical label arrays are binary. Galaxies: 16,743 paired rows, truth 0.25927253180433613; forest: 1,596 rows, truth 0.15162907268170425. Both data SHA-256 hashes match config. The target is the empirical-distribution mean under independent with-replacement draws, **not** conditional coverage on one split or validity for the original scientific population. Independent draws can share source rows; disjoint RNG draws do not mean nonoverlapping row identities.

## 2. Numeric integrity and recomputation

Across all 820,000 saved intervals:

- Nonfinite endpoints/widths/raw-widths: 0; lower>upper: 0; endpoints outside [0,1]: 0; negative reported or raw widths: 0.
- Recomputed inclusive truth containment, using analytic synthetic truths and full-precision empirical label means, agrees with all saved `covered` flags. Using rounded saved truth instead gives identical events. Coverage counts and rates reproduce summary exactly.
- Maximum |saved width − (upper−lower)| is 1.0001166561579566e-12. Maximum discrepancies against unrounded summary are 3.4938718584953676e-13 for mean width, 1.411315508903499e-12 for raw mean width, and 1.213074085626431e-11 for the paired mean-width ratio. Coverage/Wilson differences are ≤1.1102230246251565e-16. These are consistent with raw CSV export at 12 significant digits, not substantive contradictions.
- All finite-dictionary indices are in {0,…,4}, and other methods record −1. Selection is predominantly zero-control: 60,471/64,000 replicates; step-indicator control: 3,529/64,000; other controls: 0. Step/n=500 chooses indicator 1,529/2,000 times; step/n=2000 chooses it 2,000/2,000 times. All other cells choose zero-control exclusively.
- Zero-width intervals are **not automatically invalid endpoints**: they are counted as misses if they exclude truth. Every such interval here is collapsed at 0; all truths are strictly interior. Counts and raw-versus-reported collapse diagnostics are retained in the metrics CSV. `cf_rich` has one positive-raw-width collapse on forest/n=100; the unsafe in-sample negative control has six there. Raw endpoint pairs and point estimates were not saved, so untruncated containment, estimator bias/MSE and the precise original disjoint endpoints cannot be recovered from raw widths alone.

## 3. Metrics, uncertainty, and multiplicity

For each method-cell, R=2,000. Definitions:

- **Coverage**: k/R, k=Σ1{lower≤truth≤upper}. Descriptive MC SE is sqrt(p̂(1−p̂)/R); reported 95% coverage intervals are Wilson intervals, not simultaneous intervals. At nominal p=.95 the MC SE is 0.0048733971724 (about 0.487 percentage points). At 2,000/2,000 hits the plug-in MC SE is zero, but Wilson interval is [0.998082952719,1]; zero observed failures does not imply zero failure probability.
- **Width**: upper−lower after the frozen [0,1] intersection/collapse, computed from the saved `width` column and checked against endpoints to raw-export precision. Report mean, MC SE=s_w/sqrt(R), descriptive mean±1.95996398454 SE, SD and empirical 2.5/25/50/75/97.5 percentiles. `raw_width` is the separately saved untruncated width; use both, because clipping can mask very wide intervals.
- **Paired width effect**: mean width difference versus unrestricted `ppipp`, with SE=s_(w−w_ppipp)/sqrt(R). **Width ratio** is mean(w)/mean(w_ppipp), not mean(w/w_ppipp), which is undefined in zero-width replicates. Paired delta-method SE uses influence values `(w−ratio*w_ppipp)/mean(w_ppipp)` and their sample SD/sqrt(R). Ratio intervals are descriptive normal 95% MC intervals. Also save ratios and paired delta-method SE versus CP and labeled EB. These width comparisons do not establish coverage-matched efficiency.
- **Paired coverage difference** versus `ppipp`: average of the within-replicate indicator differences, with corresponding paired MC SE and descriptive normal interval.
- **One-sided exact-binomial undercoverage diagnostic**: H0: true repeated-sampling coverage≥.95, H1:<.95; boundary p-value `P[Binomial(R,.95)≤k]`. This is an exact discrete-binomial test under independent repetitions, not a normal approximation. Very small tails are evaluated via log-sum-exp of binomial log-PMFs. CSV includes `log10_p_*` and scientific-string columns; numeric p columns can underflow to zero and **must not be quoted as mathematically zero**.
- **Holm**, FWER .05, is applied jointly over every method-cell hypothesis in each tier, **not separately within each method**. Finite family: 4×32=128 (`cp`, `eb_labeled`, `eb_ppi`, `eb_select`). Asymptotic/unsafe family: 8×32=256 (all other non-oracle methods, explicitly including unsafe `insample_rich`). Oracle family: 26 synthetic cells, separately; no invented oracle cells for real data. Holm remains valid with dependent paired methods. Each tier is a separate family, not one overall FWER guarantee across all 410 tests. No additional confirmatory width-significance tests were performed; normal MC intervals are descriptive and not multiplicity-adjusted.

**Status:** designs/recipes and primary coverage/width metrics were frozen before the study. Exact test direction and tier-wide families are requested by this audit, not a retroactive preregistration. Highlighted cell explanations, paired coverage contrasts, quantiles and failure-pattern discussions are exploratory diagnostics. Tests can flag finite-n undercoverage; they cannot prove validity, establish uniformity across distributions, or refute an asymptotic theorem solely because a finite n fails.


### Tier-wise test summary

| Tier | Hypotheses | Holm rejections | Interpretation |
| --- | --- | --- | --- |
| Finite | 128 | 0 | No detected deficit; not proof of validity |
| Asymptotic + unsafe negative control | 256 | 59 | 49 non-negative-control + 10 negative-control cells |
| Oracle | 26 | 6 | Oracle control does not make Wald intervals finite-safe |

### All-method descriptive ranges

Ranges span different cells, not pooled coverage estimates.

| Method | Cells | Coverage min–max | Mean-width ratio/ppipp min–max | Holm rejections |
| --- | --- | --- | --- | --- |
| cf_linear | 32 | 0.265–0.9605 | 0.998565753529–1.06710914623 | 8 |
| cf_poly2 | 32 | 0.2645–0.9605 | 0.803997332301–1.08148482454 | 8 |
| cf_rich | 32 | 0.2645–0.971 | 0.607022718955–1.36144436711 | 5 |
| cp | 32 | 0.939–0.9965 | 1.01076975976–4.65070063205 | 0 |
| eb_labeled | 32 | 0.999–1 | 1.74426208234–13.7461367226 | 0 |
| eb_ppi | 32 | 1–1 | 2.58271338433–35.1173879889 | 0 |
| eb_select | 32 | 1–1 | 2.08580113075–18.4694683131 | 0 |
| insample_rich | 32 | 0.256–0.9615 | 0.573691922544–0.999337314212 | 10 |
| oracle | 26 | 0.2655–0.962 | 0.582173098198–1.01591354342 | 6 |
| ppi | 32 | 0.9265–0.96 | 1.00276952382–4.30232771471 | 3 |
| ppipp | 32 | 0.265–0.961 | 1–1 | 10 |
| ppipp_pkg | 32 | 0.2655–0.961 | 0.982883015833–1.05787864426 | 9 |
| wald | 32 | 0.2655–0.962 | 1.00022982083–1.7020031615 | 6 |

## 4. Claims that the numbers do and do not support

### A. Nonlinear synthetic savings; special caution for step/n=2000

Core-grid `cf_rich` results (all N/n=10):

| Scenario | n | Hits/2000 | Coverage [Wilson95%] | Width ratio/ppipp [MC95%] | One-sided p | Tier Holm p |
| --- | --- | --- | --- | --- | --- | --- |
| quadratic | 100 | 1917 | 0.9585 [0.948844451, 0.966397617] | 0.872972284993 [0.869957274, 0.875987296] | 9.66612619034e-1 | 1 |
| quadratic | 500 | 1885 | 0.9425 [0.931423726, 0.951879687] | 0.82727826117 [0.826224028, 0.828332494] | 7.0705476405e-2 | 1 |
| quadratic | 2000 | 1896 | 0.948 [0.937382046, 0.95690028] | 0.820287213092 [0.819809618, 0.820764808] | 3.54780385601e-1 | 1 |
| step | 100 | 1900 | 0.95 [0.939555891, 0.958718766] | 0.610652308043 [0.607366336, 0.61393828] | 5.14325491593e-1 | 1 |
| step | 500 | 1906 | 0.953 [0.942824558, 0.961438598] | 0.607086372647 [0.605756713, 0.608416033] | 7.44834967039e-1 | 1 |
| step | 2000 | 1871 | 0.9355 [0.923877579, 0.945452673] | 0.607022718955 [0.606377689, 0.607667749] | 2.39479661536e-3 | 4.6938013661e-1 |

At step/n=2000, width is 0.0156324445239 with MC SE 1.06732232774e-05, versus `ppipp` 0.0257526514836; reduction is 39.2977281045%. The ratio MC interval is [0.606377689235, 0.607667748676]. However, `cf_rich` misses 129/2000; coverage is **1.45 percentage points below nominal**. Its Wilson upper bound is below .95 and raw one-sided p=2.39479661536e-3, but tier Holm p=4.6938013661e-1. `ppipp` coverage in the same cell is 0.954; paired coverage difference is -0.0185 with MC SE 0.00633237115639. That contrast is descriptive/exploratory, not a separately multiplicity-adjusted superiority test. Do not claim “nominal coverage at every n” or “significant tier-wise undercoverage at step/n=2000.” Both overstate the evidence in opposite directions.

At quadratic/n=2000 the width reduction is 17.9712786908%, with coverage 0.948 and no Holm deficit detection. Width savings do not establish exact finite-sample coverage. Linear/null signals exhibit small-sample overhead (e.g., cf_rich ratios at n=30 are 1.29978310691 and 1.32535263199); quadratic/n=30 ratio is 1.06950556086, so even nonlinear gains are not uniform over n.

Analytic `oracle.csv` at N/n=10 gives width ratios 0.817389198167 (quadratic) and 0.606348643854 (step); linear/null/rare ratio is 1 (up to floating point). Its 15 rows have nonnegative variance gaps; sqrt(nvar_score_oracle/nvar_scalar) reproduces the saved ratios to 1.4432899320127035e-15. Agreement of the large-n learned width ratio with a theoretical oracle benchmark is **not** a proof that the learned interval is valid or globally optimal. Oracle normal intervals themselves reject undercoverage in six cells.

### B. Rare-event failures are substantial, but not universal across methods

`rare` has Bernoulli mean .01. All cf_rich rare cells are shown, not only the failures:

| n | N/n | cf_rich hits/2000 | Coverage [Wilson95%] | Holm p | Wald zero-width count | PPI λ=1 coverage | CP coverage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | 10 | 1262 | 0.631 [0.609620061, 0.651877673] | 2.12175311304e-416 | 732 | 0.9425 | 0.9815 |
| 500 | 10 | 1757 | 0.8785 [0.863451416, 0.89209738] | 1.00913136923e-33 | 16 | 0.9545 | 0.981 |
| 2000 | 10 | 1887 | 0.9435 [0.932505021, 0.952794558] | 1 | 0 | 0.9485 | 0.956 |
| 30 | 10 | 529 | 0.2645 [0.245634485, 0.284268445] | 8.22264767283e-1424 | 1469 | 0.934 | 0.9965 |
| 500 | 1 | 1747 | 0.8735 [0.85821202, 0.887355945] | 4.922686633e-38 | 9 | 0.9465 | 0.981 |
| 500 | 100 | 1771 | 0.8855 [0.870799779, 0.898722178] | 4.91548171646e-28 | 12 | 0.955 | 0.9835 |

Core n=100 `cf_rich` covers 1262/2000=0.631; n=500 covers 1757/2000=0.8785. At stress n=30 it covers 529/2000=.2645 (Holm p=8.22264767283e-1424). Wald has 1469/2000 zero-width [0,0] intervals at n=30, 732 at n=100, and 16 at core n=500. These failures are consistent with no-positive-label events and degenerate variance estimates; labels are not retained per replicate, so that mechanism is not independently counted from sampled labels here. Failures at n=500 also substantially exceed zero-width events, so the problem is broader than only zero variance. More unlabeled data (ratios 1,10,100 at n=500) does not repair sparse-label normal-approximation failure.

Do **not** write “every method fails on rare events”: fixed λ=1 PPI ranges .934–.955 over the six rare cells and has no tier-Holm rejection there (it is wider); CP ranges .956–.9965; all three EB recipes have full observed rare-cell coverage. At n=2000, cf_rich coverage is .9435 with Wilson [0.932505021, 0.952794558]; no adjusted deficit is detected. That is not a validity certificate either.

### C. Empirical data: no incremental nonlinear width benefit

| Scenario | n | cf_rich coverage [Wilson95%] | Width ratio/ppipp [MC95%] | ppipp coverage |
| --- | --- | --- | --- | --- |
| galaxies | 100 | 0.962 [0.952696248, 0.9695324] | 1.14565989335 [1.14020844, 1.15111135] | 0.939 |
| galaxies | 500 | 0.9525 [0.942279093, 0.960985979] | 1.02555588602 [1.02466523, 1.02644655] | 0.9495 |
| galaxies | 2000 | 0.9625 [0.953247988, 0.969978743] | 1.00646626597 [1.0062436, 1.00668893] | 0.961 |
| forest | 100 | 0.9535 [0.943370307, 0.961890931] | 1.36144436711 [1.33241444, 1.3904743] | 0.9065 |
| forest | 500 | 0.947 [0.936296617, 0.955989543] | 1.02900376019 [1.02778208, 1.03022544] | 0.937 |
| forest | 2000 | 0.9465 [0.935754264, 0.955533812] | 1.00356327233 [1.00327018, 1.00385636] | 0.9475 |

For forest/n=100, rich intervals are 36.144436711% wider than ppipp and 10.8384154586% wider than labeled CP. Their widths are 0.163900548916 (MC SE 0.00180089992858) versus ppipp 0.120387254063. Their improved point coverage cannot be separated from this substantial widening by a raw-width comparison. Forest/n=100 ppipp coverage .9065 has Holm p=1.58596543407e-13; Wald, PPI, ppipp_pkg, cf_linear, cf_poly2 and unsafe in-sample rich also reject there, whereas cf_rich does not. This is finite-n undercoverage, not failure of the empirical resampling definition.

The simpler nonlinear `cf_poly2` has no point width gain over ppipp in these six cells either (ratios 1.00000204547–1.03462117023); some tiny differences are within MC uncertainty. Claims of nonlinear real-data efficiency improvement or broad real-world coverage validation are unsupported. Scope any empirical claim to these two finite paired distributions and frozen scores.

### D. Finite-safe tiers: conservative EB, useful CP comparator, no general dominance

| Method | Coverage range | Total misses (descriptive) | Width/CP range | Width/labeled-EB range |
| --- | --- | --- | --- | --- |
| cp | 0.939–0.9965 | 2511 | 1–1 | 0.338327831732–0.579483323132 |
| eb_labeled | 0.999–1 | 8 | 1.72567520079–2.95571308716 | 1–1 |
| eb_ppi | 1–1 | 0 | 1.81150717399–8.5462080695 | 1.00863647791–3.84886203363 |
| eb_select | 1–1 | 0 | 1.62463027999–3.97133029501 | 0.941444683741–1.3436115678 |

EB-labeled has only eight misses in 64,000 intervals across different cells; EB-PPI and EB-selection have none. These totals describe these allocations, not one homogeneous binomial experiment. In step/n=2000, EB-selection width is 0.0719514623708 (SE 3.41708591715e-05) versus labeled EB 0.076426648972, ratio 0.941444683741 with paired ratio SE 0.000447051564584: 5.85553162593% narrower. This is the **only** cell where selected EB beats standalone labeled EB, and it is still 1.62463027999 times as wide as CP (paired ratio SE 0.000771465157806). In the other 31 cells selection is wider than labeled EB; selection's union-bound budget explains why a zero-control option does not imply dominance over standalone labeled EB at alpha.

EB-PPI is wider than labeled EB in all 32 cells. Clipping matters: the largest raw mean width is 2.48937897788 (EB-PPI, null/n=30), reported as width 1. Both reported and raw widths must accompany discussions of conservatism. The 2000/2000 observed hits per cell do not prove universal finite-sample validity; that requires the external bound assumptions and implementation proof.

CP's lowest coverage is forest/n=100: 1878/2000=.939, Wilson [0.927645814, 0.948671019], raw one-sided p=1.57026153076e-2, but all finite-family Holm p-values are 1. Thus neither “CP invalid because its point coverage is .939” nor “simulation proves CP valid” is warranted. All outcomes are binary in this study; these results do not transfer CP to nonbinary bounded outcomes. Conservative width comparisons alone also do not make EB unnecessary on nonbinary problems.

### E. Unsafe negative control and package baseline

`insample_rich` has ten Holm-detected undercoverage cells and must remain labeled **unsafe**, never counted as a legitimate finite-safe comparator merely because it is narrow. `ppipp` and `ppipp_pkg` are distinct frozen baselines: unrestricted paper mean recipe versus clipped-weight/package variance conventions. All width ratios in this audit use unrestricted `ppipp`, not the package replica. Package reproduction does not establish equivalence to the unrestricted recipe.


## 5. Complete familywise-significant undercoverage list

All 65 rejected method-cells, including unsafe and oracle tiers. Full-precision audit calculations from the rounded raw data, MC SEs and Wilson intervals are in the metrics CSV; extremely small p-values below are nonzero log-domain calculations.

| Tier | Scenario | n | N/n | Method | Hits/2000 | Coverage | One-sided p | Holm p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| asymptotic | step | 100 | 10 | ppipp | 1857 | 0.9285 | 1.85418138128e-5 | 3.78253001782e-3 |
| asymptotic | step | 100 | 10 | cf_linear | 1858 | 0.929 | 2.75123604937e-5 | 5.58500918022e-3 |
| asymptotic | step | 100 | 10 | cf_poly2 | 1851 | 0.9255 | 1.49751810948e-6 | 3.12981284882e-4 |
| asymptotic | rare | 100 | 10 | wald | 1266 | 0.633 | 1.2842275203e-414 | 3.12067287433e-412 |
| asymptotic | rare | 100 | 10 | ppipp | 1263 | 0.6315 | 9.50039992627e-418 | 2.34659878179e-415 |
| asymptotic | rare | 100 | 10 | ppipp_pkg | 1264 | 0.632 | 1.05270886468e-416 | 2.56860962983e-414 |
| asymptotic | rare | 100 | 10 | cf_linear | 1263 | 0.6315 | 9.50039992627e-418 | 2.34659878179e-415 |
| asymptotic | rare | 100 | 10 | cf_poly2 | 1263 | 0.6315 | 9.50039992627e-418 | 2.34659878179e-415 |
| asymptotic | rare | 100 | 10 | cf_rich | 1262 | 0.631 | 8.55545610098e-419 | 2.12175311304e-416 |
| asymptotic | rare | 100 | 10 | insample_rich | 1261 | 0.6305 | 7.68798704518e-420 | 1.91430877425e-417 |
| oracle | rare | 100 | 10 | oracle | 1266 | 0.633 | 1.2842275203e-414 | 3.21056880075e-413 |
| asymptotic | rare | 500 | 10 | wald | 1739 | 0.8695 | 5.46113344004e-44 | 1.32159429249e-41 |
| asymptotic | rare | 500 | 10 | ppipp | 1740 | 0.87 | 1.56008318672e-43 | 3.74419964813e-41 |
| asymptotic | rare | 500 | 10 | ppipp_pkg | 1739 | 0.8695 | 5.46113344004e-44 | 1.32159429249e-41 |
| asymptotic | rare | 500 | 10 | cf_linear | 1741 | 0.8705 | 4.43717165486e-43 | 1.06048402551e-40 |
| asymptotic | rare | 500 | 10 | cf_poly2 | 1742 | 0.871 | 1.25646988372e-42 | 2.99039832326e-40 |
| asymptotic | rare | 500 | 10 | cf_rich | 1757 | 0.8785 | 4.42601477732e-36 | 1.00913136923e-33 |
| asymptotic | rare | 500 | 10 | insample_rich | 1746 | 0.873 | 7.7283207425e-41 | 1.78524209152e-38 |
| oracle | rare | 500 | 10 | oracle | 1739 | 0.8695 | 5.46113344004e-44 | 1.31067202561e-42 |
| asymptotic | galaxies | 100 | 10 | insample_rich | 1854 | 0.927 | 5.43879264128e-6 | 1.1203912841e-3 |
| asymptotic | forest | 100 | 10 | wald | 1836 | 0.918 | 9.46474186936e-10 | 2.02545476004e-7 |
| asymptotic | forest | 100 | 10 | ppi | 1853 | 0.9265 | 3.56308728598e-6 | 7.37559068199e-4 |
| asymptotic | forest | 100 | 10 | ppipp | 1813 | 0.9065 | 7.27507079847e-16 | 1.58596543407e-13 |
| asymptotic | forest | 100 | 10 | ppipp_pkg | 1814 | 0.907 | 1.43341354744e-15 | 3.11050739794e-13 |
| asymptotic | forest | 100 | 10 | cf_linear | 1854 | 0.927 | 5.43879264128e-6 | 1.1203912841e-3 |
| asymptotic | forest | 100 | 10 | cf_poly2 | 1848 | 0.924 | 3.873932246e-7 | 8.13525771659e-5 |
| asymptotic | forest | 100 | 10 | insample_rich | 1792 | 0.896 | 1.29491380405e-22 | 2.83586123088e-20 |
| asymptotic | linear | 30 | 10 | ppi | 1859 | 0.9295 | 4.05314755798e-5 | 8.14682659154e-3 |
| asymptotic | linear | 30 | 10 | ppipp | 1845 | 0.9225 | 9.42392940621e-8 | 1.99787303412e-5 |
| asymptotic | linear | 30 | 10 | ppipp_pkg | 1834 | 0.917 | 3.16915428838e-10 | 6.81368172002e-8 |
| asymptotic | linear | 30 | 10 | insample_rich | 1780 | 0.89 | 6.22294511673e-27 | 1.36904792568e-24 |
| oracle | linear | 30 | 10 | oracle | 1864 | 0.932 | 2.52321471653e-4 | 5.29875090472e-3 |
| asymptotic | quadratic | 30 | 10 | ppi | 1858 | 0.929 | 2.75123604937e-5 | 5.58500918022e-3 |
| asymptotic | quadratic | 30 | 10 | ppipp | 1836 | 0.918 | 9.46474186936e-10 | 2.02545476004e-7 |
| asymptotic | quadratic | 30 | 10 | ppipp_pkg | 1852 | 0.926 | 2.31798963876e-6 | 4.82141844861e-4 |
| asymptotic | quadratic | 30 | 10 | cf_linear | 1861 | 0.9305 | 8.60857747241e-5 | 1.71310691701e-2 |
| asymptotic | quadratic | 30 | 10 | insample_rich | 1756 | 0.878 | 1.67272418403e-36 | 3.83053838143e-34 |
| asymptotic | step | 30 | 10 | ppipp | 1859 | 0.9295 | 4.05314755798e-5 | 8.14682659154e-3 |
| asymptotic | step | 30 | 10 | ppipp_pkg | 1863 | 0.9315 | 1.77605522809e-4 | 3.51658935161e-2 |
| asymptotic | step | 30 | 10 | cf_poly2 | 1845 | 0.9225 | 9.42392940621e-8 | 1.99787303412e-5 |
| asymptotic | null | 30 | 10 | insample_rich | 1819 | 0.9095 | 3.89876758946e-14 | 8.42133799324e-12 |
| asymptotic | rare | 30 | 10 | wald | 531 | 0.2655 | 8.94502191319e-1423 | 2.24520050021e-1420 |
| asymptotic | rare | 30 | 10 | ppipp | 530 | 0.265 | 1.70052661964e-1424 | 4.3023323477e-1422 |
| asymptotic | rare | 30 | 10 | ppipp_pkg | 531 | 0.2655 | 8.94502191319e-1423 | 2.24520050021e-1420 |
| asymptotic | rare | 30 | 10 | cf_linear | 530 | 0.265 | 1.70052661964e-1424 | 4.3023323477e-1422 |
| asymptotic | rare | 30 | 10 | cf_poly2 | 529 | 0.2645 | 3.22456771484e-1426 | 8.22264767283e-1424 |
| asymptotic | rare | 30 | 10 | cf_rich | 529 | 0.2645 | 3.22456771484e-1426 | 8.22264767283e-1424 |
| asymptotic | rare | 30 | 10 | insample_rich | 512 | 0.256 | 1.15028388921e-1455 | 2.94472675637e-1453 |
| oracle | rare | 30 | 10 | oracle | 531 | 0.2655 | 8.94502191319e-1423 | 2.32570569743e-1421 |
| asymptotic | rare | 500 | 1 | wald | 1743 | 0.8715 | 3.54224947339e-42 | 8.39513125194e-40 |
| asymptotic | rare | 500 | 1 | ppipp | 1744 | 0.872 | 9.94217019378e-42 | 2.34635216573e-39 |
| asymptotic | rare | 500 | 1 | ppipp_pkg | 1744 | 0.872 | 9.94217019378e-42 | 2.34635216573e-39 |
| asymptotic | rare | 500 | 1 | cf_linear | 1744 | 0.872 | 9.94217019378e-42 | 2.34635216573e-39 |
| asymptotic | rare | 500 | 1 | cf_poly2 | 1744 | 0.872 | 9.94217019378e-42 | 2.34635216573e-39 |
| asymptotic | rare | 500 | 1 | cf_rich | 1747 | 0.8735 | 2.14029853609e-40 | 4.922686633e-38 |
| asymptotic | rare | 500 | 1 | insample_rich | 1745 | 0.8725 | 2.77812615313e-41 | 6.44525267527e-39 |
| oracle | rare | 500 | 1 | oracle | 1743 | 0.8715 | 3.54224947339e-42 | 8.1471737888e-41 |
| asymptotic | rare | 500 | 100 | wald | 1760 | 0.88 | 7.97345310383e-35 | 1.80997385457e-32 |
| asymptotic | rare | 500 | 100 | ppipp | 1761 | 0.8805 | 2.07073006103e-34 | 4.65914263732e-32 |
| asymptotic | rare | 500 | 100 | ppipp_pkg | 1760 | 0.88 | 7.97345310383e-35 | 1.80997385457e-32 |
| asymptotic | rare | 500 | 100 | cf_linear | 1761 | 0.8805 | 2.07073006103e-34 | 4.65914263732e-32 |
| asymptotic | rare | 500 | 100 | cf_poly2 | 1761 | 0.8805 | 2.07073006103e-34 | 4.65914263732e-32 |
| asymptotic | rare | 500 | 100 | cf_rich | 1771 | 0.8855 | 2.2241998717e-30 | 4.91548171646e-28 |
| asymptotic | rare | 500 | 100 | insample_rich | 1762 | 0.881 | 5.3524781613e-34 | 1.18825015181e-31 |
| oracle | rare | 500 | 100 | oracle | 1760 | 0.88 | 7.97345310383e-35 | 1.75415968284e-33 |

## 6. Publication claim guidance

| Claim | Decision / defensible wording |
| --- | --- |
| “Nonlinear score controls reduce width beyond scalar PPI++.” | Supported for specified synthetic nonlinear cells; report n, ratio, coverage and MC uncertainty. Not universal. |
| “cf_rich maintains 95% finite-sample coverage.” | Unsupported; large rare-event deficits, and a step/n=2000 warning. Crossfit intervals belong to the asymptotic tier. |
| “Step/n=2000 is a Holm-confirmed violation.” | Unsupported in the requested 256-test family; raw p=.0023948 becomes .4693801. Disclose the deficit without either suppressing or upgrading it. |
| “No adjusted rejection means validity.” | False. MC power is finite; neither non-rejection nor all observed hits proves validity. |
| “Nonlinear inference improves the real-data examples.” | No incremental width benefit versus ppipp observed on either empirical distribution. Coverage sometimes improves with wider intervals. |
| “The finite-safe nonlinear method is uniformly narrower.” | Unsupported: EB-selection beats labeled EB in only one cell and never beats CP here. |
| “Oracle supplies exact-coverage intervals.” | Unsupported: the oracle control is used inside normal intervals, with six detected finite-n deficits. |
| “Every rare-event method fails.” | Unsupported: distinguish sparse-label asymptotic estimators from PPI λ=1, CP and EB. |
| “Theory is globally optimal / empirical evidence validates arbitrary populations.” | Unsupported by this design; frozen scalar-score, empirical-distribution and bounded/binary assumptions must be explicit. |

## 7. Reproducibility findings and limitations

1. **No missing cells or integrity corruption detected.** All five frozen SHA-256 checks match (`methods.py`, runner, tests, plan, amendment), both empirical data hashes match, and per-input current hashes are saved in `results_audit_provenance.json`. Matching current hashes establishes consistency with the frozen manifest; it does not independently certify the timestamp/order of that manifest or inspect every method formula.
2. **Numeric raw export is rounded** (`%.12g`), whereas summary was computed before rounding. Exact saved-data coverage counts reproduce, and tiny width/ratio mismatches are expected. Preserve 17-digit floats/binary arrays in future runs. “Exact values” here means values recomputed from the saved numeric output, not recovery of lost unrounded endpoints.
3. **No saved sampling IDs.** Preserve per-replicate labeled/unlabeled row indices or sample-array hashes and explicit child seeds to independently validate pairing without replay. Current shared-array source and rep indices are consistent, but output files alone cannot establish row identity or disjointness.
4. **No saved untruncated endpoint pairs, estimates, SEs or sample outcome counts.** Raw widths permit width auditing but not original-interval containment, point-estimate bias/MSE or direct zero-label-event auditing. These metrics cannot be invented.
5. **Summary `seconds` is cumulative since cell start at the time each method is summarized**, not that method's isolated runtime. Do not plot it as a per-method speed benchmark. Config reports overall experiment wall time; no timing experiment was rerun.
6. **Seed per cell, not a stored independent seed per replicate.** Reproducibility relies on fixed scenario ordering, loop order, RNG implementation, data hashes and dependency versions. Existing 32 seed tuples are unique. Raw file hashes are audit snapshots, not a new independent replication.
7. **MC scope and design:** repetitions are fixed at 2,000, no adaptive extension occurred here; pointwise descriptive error bars are not simultaneous. Binary target mechanisms and two empirical distributions do not span all bounded outcomes, covariate shifts or scientific populations. Model-training leakage/provenance of frozen real scores is not independently audited here.
8. **No supplemental evidence was incorporated.** A separately running exact comparator is outside this audit. Do not imply its efficiency, coverage or completion. This report makes no novelty or universal optimality claim from its absence.

## 8. Recommended next experiments (proposed only; not run)

1. Predeclare an independent, larger-seed validation of step/n=2000 and nearby n for cf_rich/oracle, with the comparison family fixed before results; include target MC precision and save sample hashes, raw endpoints and labeled event counts. Do not simply continue the current stream until a desired p-value occurs.
2. In a separate frozen rare-event study, stratify diagnostics by labeled positive count to separate zero-variance collapse from nondegenerate normal-approximation failures; retain all sparse-label cells and exact-safe comparators. No new CI recipe is justified by this analysis alone.
3. Once the independent exact-comparator study is complete, evaluate its final frozen output separately against CP/labeled EB at the same budget. Treat it as supplemental, not as part of the original confirmatory evidence. On real data, prioritize checking the near-zero incremental nonlinear benefit rather than claiming a gain.

## Artifacts and reproducible commands

- `/work/artifacts/results_audit.md`: this report.
- `/work/artifacts/results_audit_metrics.csv`: all 410 method-cells; coverage counts, uncertainty, endpoint/selection/collapse checks, width quantiles, paired effects and exact-binomial/Holm results.
- `/work/artifacts/results_audit_cells.csv`: all 32 completeness and rep-alignment checks.
- `/work/artifacts/results_audit_undercoverage.csv`: all 65 Holm-rejected method-cells.
- `/work/artifacts/results_audit_oracle.csv`: all 15 analytic rows with variance-gap/ratio arithmetic checks.
- `/work/artifacts/results_audit_provenance.json`: environment, input hashes, frozen checks, truth checks and maximum summary discrepancies.
- `/work/artifacts/audit_existing_results.py` and `/work/artifacts/render_results_audit.py`: analysis and report-rendering scripts. Reproduce with `python /work/artifacts/audit_existing_results.py` followed by `python /work/artifacts/render_results_audit.py`. Neither imports the study's methods or touches supplemental results.
- No figures were produced: this request was for an output-only audit; the machine-readable tables retain all cells without figure-level cherry-picking.

