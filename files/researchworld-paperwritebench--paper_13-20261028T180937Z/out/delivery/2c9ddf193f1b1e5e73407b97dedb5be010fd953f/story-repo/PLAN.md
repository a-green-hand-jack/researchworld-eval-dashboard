# Study plan: FoodLogAthl-218 benchmark paper

Deliverable: a complete 6-page double-column acmart (sigconf, nonacm) benchmark/dataset paper in `template.tex`
(+ `references.bib` unchanged, `figures/`, `tables/`), written from the frozen material only
(`/initial-state/inputs`: research_overview.md, tables/, figures/, AGENTS.md, references.bib). No `code/` directory was supplied;
method statements (e.g. LoRA, e5-large-v2 embedding) come only from the overview text.

## Division of work (see CODEOWNERS PR in paper-repo)
| path | owner | what |
|---|---|---|
| `template.tex` | paper-repo | the manuscript (analysis, venue, report) |
| `references.bib` | paper-repo | supplied file, unchanged (AGENTS.md: do not edit) |
| `figures/.*` | figtab-repo | the 8 supplied figures, as delivered files the paper's `\graphicspath` finds |
| `tables/.*` | figtab-repo | the 5 supplied tables, checked/rendered (the paper `\input`s them) |
| `.forgejo/CODEOWNERS` | story-repo | this split |
idea-repo supplies context (brief, related-work/cite keys); working material stays in each repo.

## Questions the paper must answer, and the evidence for each (nothing outside the supplied data)
1. Gap: web-sourced datasets (table_os: PFID, UEC-Food256, Food-101, UPMC, UNICT-FD1200, Vegfru, FoodAI-756, Food2K, Food-500 Cap) are not real logs. -> Intro/Related Work, table_os, figure distribution_5.
2. Construction (Dataset section): 11,460 imgs / 61,414 bboxes / 5,889 raw labels / 632 users, May 2023-Oct 2024 -> 6,925 / 14,349 / 218 classes / 513 users; steps in table_zn; CLIP ViT-B/16 outlier filter (>1.5 SD), manual all-or-none review, GPT-4o grouping + manual merge, two-stage PII removal, ethics + consent. Figures: thumbnail_re, error_example, histogram_linear_pdf (long tail), ACM_task (task overview, goes on page 2).
3. Validation: diversity vs UEC-Food256 (table_xj: CLIP/EVA-CLIP/Swin; Trace, Silhouette, Davies-Bouldin, Calinski-Harabasz); class imbalance; state that inter-annotator agreement is NOT reported, and that the CLIP filter may bias against hard samples.
4. Task 1 closed-set (table_kf): 10 models; best R@1 GPT-4o 0.4243 (F1 0.3732); best R@5 CLIP ViT-L/14 0.6000; LMM label via e5-large-v2 cosine matching; CLIP/EVA-CLIP lead R@5 but trail on R@1 and F1 vs LMMs -> metric choice changes the ranking.
5. Task 2 continual (all_data_1_35_with_legend, user_zero_lora_ma_wide_legend): zero-shot ~20% -> >50% with Qwen2.5-VL-3B LoRA; user-specific LoRA ~+50 pp for heavy logger "User A", eventually above all-users adaptation; weekly accuracy + weighted 1-month moving average (+-2 weeks). Read the numbers off the figures only; do not invent values.
6. Task 3 menu/description-aware (table_vs, description_eg): Qwen2.5-VL-7B F1 0.1594->0.2304, P@1 0.1019->0.1788, R@1 0.3656->0.3240; 687 errors fixed vs 1,222 new errors -> precision/recall trade-off, no net win claim.
7. Discussion: what it measures / does not (single app, single country/cuisine as far as supported, 218 merged classes from GPT-4o grouping, no IAA, user-privacy constraints).

## Inconsistencies to resolve before writing numbers (paper-repo/idea-repo to settle; the data decide, the objective's prose does not)
- table_vs "w/o description" row (F1 0.1594, R@1/3/5 0.3656/0.4590/0.4781) equals the **Qwen2-VL-7B** row of table_kf, not the Qwen2.5-VL-7B row (F1 0.2349, R@1 0.3684, R@3 0.4609, R@5 0.4859), although table_vs's caption says Qwen2.5-VL-7B. The overview also says "0.159 -> 0.230". Report table_vs as given but flag the mismatch (say the baseline row matches the Qwen2-VL-7B entry of Table X) or caption faithfully; do not silently relabel.
- table_zn step 1 shows bboxes 26,646 (-34,768) with 11,460 images; the overview merges steps 1-2 as 11,285 / 26,065. Use the table; describe steps consistently.
- table_xj header says lower Silhouette/Calinski-Harabasz mean less compact; keep arrow semantics ("harder" direction), and note CLIP Silhouette -0.0210 vs 0.0335 in the table (overview writes 0.033).
- table_kf: GPT-4o R@5 0.5221 < CLIP 0.6000; the "challenging" claim must be stated as R@1 <= 0.4243.
- Numbers in the overview ("~20% to >50%", "~50 pp") come from the figures: figtab/paper must read them off the figure, and mark them approximate.
- Citations: use only keys present in references.bib (verify with grep); no new bib entries.
- The template has a draftwatermark and `\graphicspath` must be kept; no Acknowledgements section; no Limitations/Future Work sections (limitations go in Discussion); abstract one paragraph, no math.

## Acceptance (what I check before approving CODEOWNERS-affecting changes and what review should check)
Every number in the paper traces to tables/*.tex, figures, or the overview; each of the 5 tables and 8 figures is used and cited in text; 6 pages, compiles with latexmk; Tasks, construction and findings in separate sections; limitations explicit.

## Settled decisions (answering idea-repo#brief, story-repo#3)
1. **Task 3 model label.** Write "a 7B Qwen-VL model (labelled Qwen2.5-VL-7B-Instruct in the experiment table)" and add one sentence that the no-description row coincides numerically with the Qwen2-VL-7B row of the closed-set table, so the Task 3 values are reported exactly as supplied. Never assert one reading. Table caption may keep the supplied wording; the text carries the caveat.
2. **Missing protocol details** (LoRA settings, splits, prompts, test counts, backbone of the Task 2 plots, hardware, dataset URL): state only what the overview/tables give (Qwen2.5-VL-3B LoRA for Task 2 per overview; lmms-eval; e5-large-v2 cosine matching). No invented values; where a reader would expect a detail, say plainly that it is not specified in the supplied material (once, in the setup section, not repeated).
3. **Page budget.** Main text <= 6 pages, references may follow. Priority (keep): ACM_task (Fig. 1, page 2), tables zn, kf, vs, xj (compact), table os (compact table*), histogram_linear_pdf, both Task-2 plots, description_eg (small). Shrink to one-column/combined if space: distribution_5, thumbnail_re. Drop first if needed: error_example (describe in text), then thumbnail_re. No figure/table is dropped silently: the paper must still describe what a dropped one showed. figtab-repo sets sizes/crops; paper-repo makes the final cut and tells figtab which files are unused.
4. **Approximate and attributed claims.**
   - Task 2 (all users): zero-shot ~0.23 -> ~0.16, full FT ~0.24 -> ~0.51, LoRA ~0.26 -> ~0.49 (read off the plot). The overview's ">30 pp" holds only as the gap to zero-shot at the end of the period (~0.16 vs ~0.5); state it that way, not as a gain from initial accuracy (that is ~+25 pp).
   - User A: zero-shot ~0.14 -> ~0.08; all-users LoRA ~0.29 -> ~0.65; user-only LoRA ~0.17 -> ~0.6. User-only LoRA exceeds all-users LoRA over roughly 2023/08-2023/12 but is below it at the last point: do NOT write "eventually surpasses all users". "~+50 pp" is relative to zero-shot at the end; weekly values are noisy.
   - "687 corrected / 1,222 new errors" appears only in the study text, not in a table: report it as stated by the study, once, with no derived percentages.
   - Task 1: the "challenging" claim is R@1 <= 0.4243 (GPT-4o) and best R@5 0.6000 (CLIP ViT-L/14); CLIP/EVA-CLIP lead at R@5 but trail LMMs at R@1.
   - No bib entry for Qwen2-VL/Qwen2.5-VL/LLaVA-OneVision/LLaVA-NeXT: cite only existing keys (bai2023qwen, liu2024improved, ...); never create entries. Remove the template's Acknowledgements section.
