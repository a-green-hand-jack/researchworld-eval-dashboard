# Review of version 1 — `paper-repo` PR #13 (main → release)

Head inspected: `3b1a5c2faaf5acaacbf0857d670aa26fe7c6e37c`. Standard: `REVIEW_STANDARD.md`.
Conclusion: **approved**. Every requirement of the objective is met and the evidence supports the claims.

## What I inspected
- **Reproduction:** I copied the delivered `code/`, `outputs/` and `report/` into a clean tree, with `data/glambie` linked read-only to `/initial-state/inputs/2/glambie`.
  - `python code/run_all.py` ran in 1 min 44 s. Its output matches the delivered `outputs/reconciliation` and `outputs/validation` exactly (`diff -rq` empty).
  - `python code/figures/make_all.py` produced all seven PNGs byte-identical to the delivered ones, and `outputs/tables/` unchanged.
- **Delivery check:** the `hutian/delivery` status is `success` at the head. All 7 image links in `report/report.md` resolve to nonempty PNGs.
- **Figures F1–F7:** I opened every one. Each has labelled axes with units, a legend, panel titles and readable text, and none is a placeholder. Each shows what its caption and the text claim:
  - F1: coverage, and used/submitted counts that sum to 167/257.
  - F2: group series and the consensus for all 19 regions.
  - F3: annual and cumulative global series against GlaMBIE, with sea-level equivalent.
  - F4: regional ranking and period rates.
  - F5: 25/27 group pairs agree within 2σ; the two red pairs are the ones named in §4.3.
  - F6: validation scatter plots, regional acceleration attribution, and prior estimates.
  - F7: sensitivity.
- **Units** (`code/analysis/homogenise.py::to_mwe_gt`): `unit.lower()` handles both `Gt` and `gt`. Elevation change `m` is converted with 850 ± 60 kg m⁻³ and the density error added in quadrature.
- **Area:** taken from the GlaMBIE result files, which is disclosed (§2 and Limitation 4). The 2000 global area is 704,083 km², the same as the reference.
- **Time:** hydrological-year starts match the reference files: 0.75 in the north, 0.25 in regions 17–19, 0.0 in region 16. The method for converting to calendar years is described.
- **Gravimetry:** the reference files carry gravimetry only in regions 1, 3, 4, 6, 7, 9 and 17. The study keeps it in exactly those and tests it elsewhere as a sensitivity variant.
- **Required outputs:** `outputs/reconciliation/regional_calendar_years.csv` and `regional_hydrological_years.csv` give mwe, mwe_err, gt and gt_err per region and year. `global_calendar_years.csv` gives the global series. Both cover 2000–2023.
- **Numbers spot-checked against the files:**
  - global 2000–2023: −6615 ± 270 Gt, −275.6 ± 11.2 Gt/yr, −0.409 ± 0.017 m w.e./yr, 18.2 ± 0.7 mm, with a correlated bound of ±1309 Gt;
  - sub-period rates −251.3 ± 15.3 and −299.9 ± 16.4 Gt/yr;
  - all 19 rows of Table 2 against `summary_regional.csv`;
  - 25/27 agreeing group pairs;
  - Birge ratios against `group_diagnostics.csv`;
  - prior estimates against `prior_estimates.csv`.
- **Prior estimates:** I checked them against the related-work PDFs. Hugonnet et al. (2021) Table 1 gives −227 ± 25, −257 ± 22, −284 ± 23 and −292 ± 24 for 2015–2018 (the "a" footnote periods). The abstract gives −267 ± 16 and an acceleration of 48 ± 16 Gt/yr per decade. Zemp et al. (2019) gives −335 ± 144 for 2006–2016. All are quoted correctly.
- **Comparison with my reference values** from `data/glambie/results/calendar_years/0_global.csv`:
  - GlaMBIE: −6542 ± 387 Gt; −231 and −314 Gt/yr for the two sub-periods.
  - The study: −6615 ± 270 Gt; −251 and −300 Gt/yr.
  - The weaker acceleration (+19 % against +36 %) is reported prominently. It is attributed by region in Fig. 6c and §6. Equal group weights are tested, and the report states that they do not close the gap.

## External-review reading (what a referee would still ask; none blocks this version)
1. **Uncertainty:** the headline ±270 Gt assumes independent annual errors and independent regions. The report gives the correlated bound (±1309 Gt) and shows that structural sensitivity (±10–28 Gt/yr) is as large as the 1σ. A referee might want a combined structural plus random interval in the headline itself.
2. **Trend uncertainty:** the "−93 ± 28 Gt/yr per decade" is an ordinary least-squares error. It ignores the stated annual errors and autocorrelation, though the report does call it a statistical fit.
3. **File count:** the gap between 257 files and the 233 cited estimates is disclosed but not explained. The likely cause is several solutions submitted per group, but this is not shown.
4. **Annual allocation:** the annual split in 2000 and 2013–2014 depends on the glaciological variability and the seasonal correction. Model users should calibrate on multi-year rates where annual agreement is low; the report says so (§6, "Use as a benchmark").
