# Sizing note (acmart sigconf: column 3.33 in, text width 7.0 in)

Height of each figure at column / full width, and approximate rendered text size of its smallest labels
(source font px / (image width px / placed width in) / 72*... measured by eye on the 90-dpi preview).

| figure | col h (in) | full h (in) | verdict |
|---|---|---|---|
| ACM_task | 2.74 | 5.75 | use full width at ~0.62 of width (about 3.6 in tall) or column if space is tight; labels legible at column |
| all_data_1_35_with_legend | 1.46 | 3.07 | column width OK (legend/ticks about 6 pt) |
| user_zero_lora_ma_wide_legend | 1.83 | 3.84 | column width OK |
| description_eg | 1.97 | 4.14 | column width OK (text about 6 pt); full width if space |
| distribution_5 | 1.21 | 2.54 | must be full width (`figure*`): at column width the text is about 3 pt |
| histogram_linear_pdf | 1.54 | 3.23 | column width legible; first cut candidate |
| thumbnail_re | 2.25 | 4.74 | column width; the five coloured borders have no legend in the image |
| error_example | 0.96 | 2.02 | full width (`figure*`) is most readable; or column, labels ~5 pt |

Cut order proposed by story-repo if the 6-page limit forces it: error_example (0.96 in at column), histogram_linear_pdf (1.54 in),
distribution_5 (2.54 in full width; or fold into a 2-panel figure with the histogram).
Tables: kf, vs single column (fit 241 pt with tabcolsep 3 pt); xj, zn, os page width.
