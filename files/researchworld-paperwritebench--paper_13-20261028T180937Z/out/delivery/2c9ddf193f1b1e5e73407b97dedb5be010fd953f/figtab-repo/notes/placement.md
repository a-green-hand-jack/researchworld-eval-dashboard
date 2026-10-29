# Suggested sizes (acmart sigconf: column 3.33 in, full width 7 in); paper-repo makes the final cut

| file | use | height at that width | legibility at that size |
|---|---|---|---|
| ACM_task.jpg | `figure` (column) on page 2, or `figure*` at ~0.6\textwidth | 2.74 in at column | text is large; legible at column width |
| distribution_5.jpg | `figure*` at 7 in (2.54 in tall); at column width the 6-column row is too small to read | 2.54 in | only legible full width; drop or shrink to ~5 in if short of space |
| thumbnail_re.jpg | column (2.25 in) | 2.25 in | fine (photo grid) |
| error_example.jpg | column (0.96 in) | 0.96 in | fine; cheapest figure |
| histogram_linear_pdf.jpg | column (1.54 in) | 1.54 in | legible |
| all_data_1_35_with_legend.jpg | column (1.46 in), or both Task-2 plots side by side in a `figure*` at 3.4 in each | 1.46 in | legible; big fonts survive downscaling |
| user_zero_lora_ma_wide_legend.jpg | column (1.83 in) | 1.83 in | legible |
| description_eg.jpg | column (1.97 in); text inside is small, do not go below column width | 1.97 in | borderline; keep at full column |

Tables: table_kf, table_vs are single-column (`\resizebox{\columnwidth}`); table_os, table_zn, table_xj are `table*` (about 1.2 / 1.3 / 1.1 in tall at 9 pt). Reference widths with `\includegraphics[width=\columnwidth]{...}`; the files need no cropping. Every file stays in `figures/` whether or not the text uses it; tell figtab-repo which are unused and they will be removed.
