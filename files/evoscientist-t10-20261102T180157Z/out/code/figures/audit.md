# Figure audit

- script_ran: yes; final `python plot.py` completed without error.
- png_exists: yes for efficiency, validity, coverage_all, all300dpi.
- chart_type_matches_spec: pass; paired line/errorbar panels and complete coverage heatmap.
- data_columns_match_spec: pass; all data read from generated CSV, literal null retained.
- axis_scales_match_spec: pass; n logarithmic, ratios/coverage linear. Validity y range contains smallest plotted rare-event coverage.
- labels_units_match_spec: pass; different references explicitly labeled in two efficiency panels and captions.
- series_category_order_match_spec: pass; seven core distributions included,32heatmap cells,missing real oracle gray.
- legend_complete_and_uncropped: pass; efficiency legend moved below panels and assets regenerated, distinct marker shapes added.
- annotations_match_spec: pass; reference ratio1 and coverage.95,paired MC intervals/Wilson intervals, no fitted smoothing.
- forbidden_elements_absent: pass; no invented data, extrapolation, unrequested regression line or hidden off-scale points.
- obvious_text_overlap_or_clipping: pass on PNG inspection and final layout checks; dense heatmap values are supplementary, full precision inCSV.
- repairs_made: roundoff-only negative display errorbars clamped tozero; legend/sourceasset synchronization; marker differentiation; paperPDF export throughPGF for embeddedType1fonts.
- remaining_warnings: PNG uses Matplotlib text fonts while paperPDF uses TeXType1; data and graph layout are identical. Heatmap two-decimal values must not decide nominal validity.
- final_status: REPAIRED
