# Captions and claims (presentation of FoodLogAthl-218)

Status: figure files marked *as supplied* are the frozen inputs, unmodified; items marked *generated* come from `code/figtab/make_figs.py` using only the numbers in the supplied tables. Open points are tracked in figtab-repo#2 / paper-repo#5.

| Item | File | Claim it supports | Caption (draft) | Status |
|---|---|---|---|---|
| Fig: benchmark contrast | `figures/distribution_5.jpg` | Real logs differ from web-crawled datasets on five axes (label-after-image, imbalance, low aesthetic bias, temporal continuity, multi-dish) | Traditional web-built food datasets vs. FoodLogAthl-218 along five properties. | as supplied; page 2 candidate |
| Fig: tasks | `figures/ACM_task.jpg` | Definition of the three tasks | Overview of the three tasks. | **empty boxes: needs fix** |
| Fig: examples | `figures/thumbnail_re.jpg` | Dataset content: casual, multi-dish, imbalanced | Examples included in FoodLogAthl-218. | as supplied |
| Fig: class histogram | `figures/histogram_linear_pdf.jpg` | Long-tailed class frequency (10 to ~1.7k images/class) | Number of dish classes (vertical) by images per class (horizontal, log). Arrows mark illustrative classes. | as supplied; arrows unexplained, unit unclear |
| Fig: errors | `figures/error_example.jpg` | Why manual review was needed (wrong label, wrong box, inappropriate image) | Examples of erroneous records removed or fixed during curation. | as supplied |
| Fig: Task 1 | `figures/task1_recall_f1.pdf` | LMMs lead at R@1 (GPT-4o best on F1/R@1/R@3), CLIP-family leads at R@5 (0.594/0.600 vs 0.522) | Task 1: R@1/3/5 and F1 per model. | generated from table_kf |
| Fig: curation funnel | `figures/curation_funnel.pdf` | 11,460→6,925 images, 61,414→14,349 boxes, 5,889→218 classes | Counts after each curation step. | generated from table_zn |
| Fig: Task 2 all users | `figures/all_data_1_35_with_legend.jpg` | Continual adaptation: zero-shot declines (~0.23→~0.16) while fine-tuning rises to ~0.5 | Weekly accuracy (dashed) and weighted ±2-week moving average (solid). | as supplied; model, weekly n, range (ends Jan 2024) unstated |
| Fig: Task 2 User A | `figures/user_zero_lora_ma_wide_legend.jpg` | User-specific LoRA overtakes all-user LoRA for a heavy logger | Same for User A. | as supplied; duplicated "2023/10" tick, tiny weekly n, no counts |
| Fig: Task 3 example | `figures/description_eg.jpg` | How the menu description changes predictions | Examples for description-guided classification. | as supplied |
| Tab: curation | `tables/table_zn.tex` | Pipeline counts | step 6 class Δ printed as −962 (supplied: −982; 1,180−218=962) | restyled; **correction pending owner** |
| Tab: Task 1 | `tables/table_kf.tex` | as Fig: Task 1 | | restyled |
| Tab: Task 3 | `tables/table_vs.tex` | Menu text raises F1 0.159→0.230 and P@1 0.102→0.179 but lowers R@1 0.366→0.324 | | restyled; **model name of this row matches Qwen2-VL-7B in table_kf, not Qwen2.5-VL-7B — pending owner** |
| Tab: diversity | `tables/table_xj.tex` | Higher spread / lower separability than UEC-Food 256 across 3 extractors | | restyled |
| Tab: datasets | `tables/table_os.tex` | Only app-sourced dataset | | restyled; unit of #samples per dataset pending |
