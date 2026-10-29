# Review standard for the GlaMBIE reconciliation study

Owner: `internal-review-repo` (review + external-review). Taken from the objective
(`internal-review-repo#1`, `/initial-state/inputs/1/INSTRUCTIONS.md`), the supplied data
(`data/glambie`, DOI 10.5904/wgms-glambie-2024-07) and the related work (Zemp et al. 2019,
Hugonnet et al. 2021, Rounce et al. 2023, Hock et al. 2019, Marzeion et al. 2020).

A version is approved only if every item below holds at the pull request's head commit.

## A. Required outputs (objective)
1. Annual time series 2000–2023 for each of the 19 RGI regions **and** global, with
   uncertainties, in both specific mass change (m w.e.) and total mass change (Gt),
   delivered as files under `outputs/` and produced by code under `code/`.
2. The series are **derived by the study from the 233 input estimates in `data/glambie/input`**
   (unit harmonisation, temporal homogenisation, per-method/data-group combination,
   inter-method combination, regional → global aggregation). Copying
   `data/glambie/results` as the result is not a reconciliation; the supplied results may and
   should be used as an independent check of the study's own output.
3. Uncertainties are propagated with a stated, defensible model (per-estimate errors,
   method/group spread, density-conversion error, area error, correlation assumptions for
   temporal sums and regional → global sums) and stated for every headline number.

## B. Correctness checks I will run myself
4. Units: inputs mix `Gt`, `gt`, `m` (elevation change) and `mwe`; `m` needs a stated
   density conversion (e.g. 850 ± 60 kg m⁻³) and m w.e. ↔ Gt needs a stated, time-varying
   glacier area with provenance. Case variants of `Gt` must not be dropped.
6. Time: inputs are on hydrological years (region-specific) or multi-year periods; the
   conversion to annual and to calendar years for global aggregation is described and
   validated. Multi-year-only sources (DEM differencing) contribute to trends, not
   fabricated annual variability, unless the variability source is stated.
7. Per-region coverage table: number of estimates per method per region, which were used
   and which excluded, and why.
8. Reproduction: I re-run the delivered code from the delivered tree and get the delivered
   `outputs/` numbers (within rounding).
9. Validation: per-region and global comparison with the supplied GlaMBIE results
   (bias, RMSE/agreement within uncertainties), and comparison with prior work in
   `related_work` (e.g. Hugonnet et al. 2021, 2000–2019: −267 ± 16 Gt/yr; Zemp et al. 2019).
   Reference values I computed from `data/glambie/results/calendar_years/0_global.csv`:
   cumulative 2000–2023 ≈ −6542 ± 387 Gt, mean ≈ −273 Gt/yr, 2000–2011 mean ≈ −231 Gt/yr,
   2012–2023 mean ≈ −314 Gt/yr. Large deviations must be explained, not hidden.
10. Method agreement analysis: inter-method differences per region (the "reconcile"
    part of the objective), with whether they are within the stated uncertainties.

## C. Report (`report/report.md`)
11. Methodology, results, discussion, limitations; academic style; every number in the
    text traceable to a file in `outputs/`.
12. Figures (PNG in `report/images/`, linked as `images/<name>.png`): at minimum a data
    overview (coverage of estimates by method/region/time), main results (global and
    regional annual series with uncertainty bands, cumulative Gt and m w.e.), and
    validation/comparison plots. I open every figure: axes labelled with units, legends,
    readable, no placeholders, and each shows what the text claims.
13. Headline claims (acceleration, regional ranking, sea-level equivalent if stated with
    362.5 Gt per mm) carry uncertainty and a stated test/assumption.
14. Relevance to the objective's purpose (benchmark for IPCC / model calibration) is
    discussed, including limits of use.

Anything that the inputs cannot yield, shown by an attempt, is recorded as a limitation;
work not done is a finding.
