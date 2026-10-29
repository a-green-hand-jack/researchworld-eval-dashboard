# figtab-repo: delivered figures and tables

Delivered paths (merged into `paper-repo` by pull request): `figures/*.jpg`, `tables/*.tex`.
Generator code: `figures/generator/label_task_overview.py` (the only figure that was changed). Tables were edited by hand from the supplied sources;
every change is listed below. Inputs: `/initial-state/inputs/4/*.jpg`, `/initial-state/inputs/8/*.tex`. No underlying data series or `code/` was supplied,
so the plots could not be re-rendered; they are delivered as supplied.

## Changes to supplied files
- `figures/ACM_task.jpg`: the supplied image had four empty boxes and an unlabeled input arrow. Filled with: "Free-form dish description" (LMM output, Task 1),
  "Predicted label", "Class names (218 classes)" (text-encoder input), "Description of the entire image (all dishes)" and "Dish label" (Task 3).
  Texts follow the overview (LMM description -> e5 embedding -> cosine match to class names) and `description_eg.jpg` (Q1 whole image, Q2 crop + description). Nothing else in the image touched.
- other 7 figures: byte-identical copies.
- `table_zn.tex`: **corrected arithmetic typo**: step 6 class change was printed -982; 1,180 -> 218 is -962 (all other diffs re-checked and correct). Re-laid out without the `r@{ (}` column hacks; same numbers.
- `table_kf.tex`: rows sorted by R@1, added `Type` column (LMM/CLIP), numbers unchanged, bold unchanged (all verified as column maxima).
- `table_vs.tex`: added a computed $\Delta$ row (F1 +0.0710, P@1 +0.0769, R@1 -0.0416, R@3 -0.0558, R@5 -0.0445); caption states the baseline-row mismatch (below); `resizebox` added (single column).
- `table_xj.tex`: caption says what the arrows/bold mean (more spread, not "better"), class counts differ (218 vs 256), single computation; fixed `\cmidrule{11-13}` -> `(l)`.
- `table_os.tex`: caption + footnote that ours counts bboxes (6,925 images); footnote moved inside the tabular (no `itemize`); same cite keys (all 12 verified present in references.bib).
- Labels unchanged: `table:classification_comparison`, `table:desc_guided`, `table:diversity_metrics_comparison`, `data cleaning steps table`, `Food image dataset table`.
- Build check: tables + a figure compiled in a stand-in two-column 9pt/7in class (no overfull boxes). **acmart is not installed in this sandbox** (`kpsewhich acmart.cls` empty), so the final acmart layout was not built here.

## Data inconsistencies found (to be disclosed by the paper, not silently resolved)
1. `table_vs` "w/o description" (F1 .1594, R@1/3/5 .3656/.4590/.4781) is identical to the **Qwen2-VL-7B** row of `table_kf`, while its caption says Qwen2.5-VL-7B (whose row in table_kf is .2349/.3684/.4609/.4859). Either label is wrong; which one cannot be settled from the supplied material.
2. `table_zn` step 1: 61,414 -> 26,646 bboxes with images unchanged at 11,460; the overview merges steps 1-2.
3. `table_os`: "#samples" is images for the other datasets but bboxes for ours (14,349 bboxes in 6,925 images).
4. Task 3 consistency check (derived, not reported): 1,222 new errors - 687 corrected = net +535 errors, and R@1 fell by 0.0416, which implies an evaluation set of about 12.9k dishes. That is plausible next to 14,349 bboxes, but the evaluation-set size is not stated anywhere.

## Read-offs from the Task-2 figures (approximate, ±0.02, read from pixels; no series supplied)
`all_data_1_35_with_legend.jpg` (weighted moving average, last point; y-axis 0-0.7): Full finetune ~0.51, LoRA finetune ~0.49, Zero-shot ~0.16. First points ~0.24 / ~0.26 / ~0.23.
- The overview's "from ~20% to >50%" for LoRA is **not supported by the moving average**: LoRA ends at ~0.49 (weekly values reach ~0.55 once); only Full finetune ends above 0.5. "LoRA gain >30 pp" holds against the zero-shot curve at the end (~0.49 - ~0.16 = ~0.33), not against its own start (~+0.22). Zero-shot itself drifts down from ~0.23 to ~0.16.
- x-axis ends 2024/01 although the dataset spans May 2023-Oct 2024; the figure covers only part of the span. The fine-tuned model/backbone behind "Full finetune" is not named in the supplied material (the overview names Qwen2.5-VL-3B for LoRA).

`user_zero_lora_ma_wide_legend.jpg` (User A, moving average; y-axis 0-1):
- LoRA(user only) rises ~0.17 -> ~0.6-0.65 (peak ~0.67); zero-shot stays ~0.06-0.14; gain over zero-shot ~+0.5 from about Sep-Dec 2023 (~0.57-0.65 vs ~0.09).
- User-only is **below** all-users LoRA until about 2023/07 (all-users ~0.3-0.4 vs user-only ~0.2 in May-June), above it from about Aug to Dec (by ~0.05-0.15), and **below again in the last 2 points** (all-users ~0.65-0.69 vs ~0.57-0.63). So "eventually surpassing all-users adaptation" is true only for the middle of the period; do not claim it without that qualification.
- Weekly (dashed) values swing between 0.0 and ~0.8 for a single user: small weekly n, no uncertainty shown; claims should rest on the moving average and say so.
- Tick labels are every fourth weekly point labeled by month only, so "2023/10" appears twice (a labeling artifact, not a data error).

## Caption facts for the paper (checked against the figures)
- `ACM_task`: Task 1 closed-set (LMM description -> text encoder -> cosine similarity vs class names); Task 2 incremental training on accumulating data, test on the following period; Task 3 menu-aware (description of whole image, then crop + description).
- `description_eg`: left "Successful" = crop alone wrong (Dumplings -> Okonomiyaki), with description right (Dumplings); right "Unsuccessful" = crop alone right (Vegetable_Juice), with description wrong (Egg Soup). I.e. the labels refer to the effect of the description.
- `histogram_linear_pdf`: the filename says linear but the x-axis (number of images per class) is logarithmic, 10^1 to >10^4 axis range, y = number of dish types; classes range from 10 images (16 classes at the minimum) up to ~2x10^3; arrows mark example classes. The x label says "images" (not bboxes). The axis extends to 10^4 with no data beyond ~2x10^3.
- `thumbnail_re`: 24 sample images; the 5 coloured frames (magenta, yellow, green, cyan, red) are not explained in the supplied material, so the caption must not interpret them unless the text owner knows their meaning.
- `error_example`: three error types: incorrect label, incorrect bbox, inappropriate image (empty plate labeled Milk; packaging label for Donut).
- `distribution_5`: conceptual comparison (data source, label-after-image collection, natural imbalance, low aesthetic bias, time-series continuity, multi-dish meals); the bar charts are schematic, not measured data; say so in the caption.
