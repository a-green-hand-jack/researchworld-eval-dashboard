# Review of the final version — `paper-repo` PR #17 (main → final)

Head inspected: `5a3c88bb4bde9502af8b1c5b377bd805df4ac084`. Changes since the approved v1 (`3b1a5c2`): `code/README.md`, `code/run_all.py`, the new `outputs/validation/headline_uncertainty.json`, and `report/report.md`. Figures and the other outputs are unchanged (`git diff --stat` empty).

## What I inspected
- **Reproduction:** `python code/run_all.py` in a clean tree with read-only data. The whole of `outputs/` matches what was delivered (`diff -rq` empty), including `headline_uncertainty.json`. The `hutian/delivery` status is `success`.
- **Combined headline uncertainty:**
  - 2000–2023 rate: ±17.3 = √(11.2² + 13.2²) Gt/yr.
  - Increase between periods: 49 ± 24 = √(22.4² + 9²) Gt/yr.
  - Sub-period rates: ±19.6 and ±22.4 Gt/yr.
  - The cumulative totals (±414 Gt, ±1.1 mm) are consistent with these.
  - The definition is stated, the random-only values are kept alongside, and a narrower variant set (±13.6) is given.
- **Trend:** the JSON gives:
  - WLS −92.8 ± 39.8 per decade (Birge 1.83, AR(1) 0.31, n_eff 12.8), combined with the structural SD as −92.8 ± 40.0;
  - OLS with AR(1) −82.1 ± 40.4.
  The report text at §4.1 matches. The rewording of the Hugonnet comparison (not significantly different) is correct.
- **257 vs 233 (§2):** the wording is accurate to the supplied documentation and does not overclaim.

## Finding (blocks `final`, owner `paper-repo`)
1. **§3.5 contradicts §4.1.** `report/report.md` line 67 says acceleration is quantified "by the slope of an **ordinary least-squares** fit to the annual global mass change". The reported trend (−93 ± 40 per decade, line 94) is the **weighted** least-squares slope, and line 94 says the unweighted (ordinary) fit gives −82 ± 40. The Methods must describe the estimator actually reported: WLS on the annual 1σ, with the error inflated by the Birge ratio and AR(1), combined with the structural SD; the OLS value given as an alternative. Table 3's trend column (main −93) uses the same WLS estimator, so the method sentence should cover it too.

## Non-blocking
- The Fig. 3a title and Tables 1 and 2 give random-only errors (±11.2 Gt/yr, ±270 Gt), while the abstract and conclusions give combined ones. The captions and footnotes do say "independent annual errors". A reader would be helped by one clause, e.g. in the Table 1 footnote, pointing to the combined values.

## Re-review at head `055e87dbf5aed0c6d3c721dac36c68acdbcb08e0`
- **Change since `5a3c88b`:** one line in `report/report.md` (§3.5). It now describes the trend as a weighted least-squares fit, with the error inflated for excess scatter and lag-1 autocorrelation and combined with the structural spread. This matches §4.1, `headline_uncertainty.json` (`recommended`) and the Table 3 trend column. §4.1 keeps the OLS alternative (−82 ± 40). Finding 1 is resolved.
- **Everything else** in the tree is byte-identical to `5a3c88b`, which I reproduced in full. The `hutian/delivery` status is `success`.
- The non-blocking note on random-only errors in Tables 1 and 2 and Fig. 3a stays as a note. Those values are labelled as independent-annual-error values.
- **Conclusion: approved for `final`.**

## Re-review at head `43dc8e382bcbe152b448d42457a96f3795610757`
- **Change since `055e87d`:** two lines of `report/report.md`. §3.5 now names OLS (with AR(1)) as the alternative estimator. The Table 1 footnote now marks its errors as random-only and gives the combined values: ±414 Gt, ±17.3 Gt/yr, ±0.026 m w.e./yr, ±1.1 mm, and ±19.6 / ±22.4 Gt/yr for the sub-periods. It cites `headline_uncertainty.json`. Each value matches the JSON I checked at `5a3c88b`. This settles the non-blocking note for Table 1.
- **Nothing else changed.** The `hutian/delivery` status is `success`.
- **Conclusion: approved for `final`.**
