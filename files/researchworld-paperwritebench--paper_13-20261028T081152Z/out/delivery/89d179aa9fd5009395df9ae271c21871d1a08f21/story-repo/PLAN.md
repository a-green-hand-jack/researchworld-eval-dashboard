# Study plan: FoodLogAthl-218 benchmark paper

Type: benchmark / dataset paper (see `AGENTS.md` in the frozen inputs: no method framing, state what the benchmark does and does not measure, report mixed results as they are). Target: 6-page double-column `acmart` sigconf, `template.tex` + `references.bib`, figures in `figures/`, tables in `tables/`.

## Division of work (CODEOWNERS, `paper-repo` PR #2)
| Path | Owner | Function |
|---|---|---|
| `template.tex`, `references.bib` | paper-repo | analysis (checking numbers against the supplied tables/figures), venue (6 pages, acmart, no Acknowledgements, keep `\graphicspath`), report |
| `figures/*`, `tables/*` | figtab-repo | presentation: each figure/table shown for the claim it supports, in 6-page budget |
| `.forgejo/CODEOWNERS` | story-repo | this plan |
| context (brief, prior work, related-work bib keys) | idea-repo | supplies paper-repo and me, no delivered path |
| review | internal-review-repo | approves merges into `release`/`final` |

No new experiments are possible or required: the evidence is the frozen `tables/` and `figures/` (the `code/` folder named in the task is not among the supplied inputs). "Analysis" therefore means a faithful, checked reading of those results (claim-to-evidence audit, derived quantities such as differences), not new training runs.

## Questions and the evidence that answers them
| # | Question / claim | Evidence | Section |
|---|---|---|---|
| Q1 | How is the dataset built and how much does each curation step remove? | `table_zn` (11,460 -> 6,925 images; 61,414 -> 14,349 bboxes; 5,889 -> 3,071 -> 1,180 -> 218 classes), `error_example`, `thumbnail_re` | Dataset |
| Q2 | How does it differ from existing food datasets (source, scale, real-world conditions)? | `table_os`, `distribution_5`, `histogram_linear_pdf` (long tail) | Intro/Related/Dataset |
| Q3 | Is it more diverse/harder than UEC-Food 256 in feature space? | `table_xj` (Trace, Silhouette, DB, CH x CLIP/EVA-CLIP/Swin) | Dataset analysis |
| Q4 | Task 1: how hard is closed-set classification? | `table_kf` (GPT-4o R@1 .4243 F1 .3732; CLIP ViT-L/14 R@5 .6000; EVA-CLIP best R@5 among non-GPT apart from CLIP) | Experiments |
| Q5 | Task 2: does continual adaptation help, and does personalisation? | `all_data_1_35_with_legend`, `user_zero_lora_ma_wide_legend`, `ACM_task` | Experiments |
| Q6 | Task 3: does menu/description context help? | `table_vs` (F1 .1594->.2304, P@1 .1019->.1788, R@1 .3656->.3240, R@3 .4590->.4032, R@5 .4781->.4336), `description_eg` | Experiments |

## Checks the report must pass (found in reading the inputs; paper-repo owns the resolution)
1. **Table/baseline inconsistency.** `table_vs` is captioned Qwen2.5-VL-7B-Instruct, but its "w/o description" row (F1 .1594, R@1 .3656, R@3 .4590, R@5 .4781) equals the *Qwen2-VL-7B-Instruct* row of `table_kf`; the Qwen2.5-VL-7B row there is F1 .2349, R@1 .3684. Do not claim both; report the numbers as supplied, state which model the description experiment is, and flag the mismatch (ask idea-repo/ht-human if resolvable; otherwise say it in the text neutrally or label the model by what the table supports). Note: with F1 .2349 as the baseline, "description improves F1" would be a much smaller gain (.2349 -> .2304 is a decrease), so this matters for the Task 3 claim.
2. **Unsupported numbers in the overview.** "Corrects 687 errors while causing 1,222 new errors", "~20% to >50% (>30 pp)", "~50 pp for a heavy logger, eventually surpassing all-users adaptation" are not in any table; use them only if readable from a figure/caption; otherwise omit or mark approximate. 687/1,222 can be used only as attributed to the supplied overview if figtab/idea confirm a source.
3. **`table_os`** lists FoodLogAthl-218 "#samples" = 14,349, which counts bounding boxes (images: 6,925); other rows are image counts or mixed units. Caption/footnote must say so. Also `table_xj` heading says lower Silhouette/CH = less compact; keep the "higher difficulty" claim to feature-space spread, not human difficulty.
4. **Step 1 of `table_zn`** is "remove samples w/o image" (bboxes 61,414 -> 26,646, classes 5,889 -> 3,167); the overview merges steps 1-2. Use the table.
5. **Honesty items from the objective:** inter-annotator agreement not reported; dataset from a single app/population (Japanese-style cuisine dominates is NOT supplied: do not assert it); user-aware Task 2 shown for one heavy logger (User A) only; Task 3 trades recall for precision.
6. Claims on "public" release, licence, URL and ethics approval: state only what the overview gives (ethics approval, informed consent, two-stage PII removal); no invented URL or IRB number.

## Order of work
1. idea-repo: Brief + related-work bib keys. 2. figtab-repo: render/verify the tables and figures with the claims above (can start now). 3. paper-repo: draft `template.tex` against this table, run `latexmk` to check 6 pages, submit PR into `main`. 4. internal-review-repo reviews; paper-repo proposes version into `release`, then `final`.

## Decisions on the inconsistent source material (answering idea-repo#4 on story-repo; supersede the corresponding checks above)
1. `table_zn` step 6 class diff: the delivered table prints **-962** (1,180 -> 218). Owner of the fix: figtab-repo.
2. `table_zn` steps 1-2: merge into one row "Remove samples w/o image or bounding box" = 11,285 (-175) images, 26,065 (-35,349) bboxes, 3,071 (-2,818) classes (sums of the two printed rows; also what the overview states). Remaining steps are renumbered. The text never says the image-removal step removed bboxes alone. Owner: figtab-repo (table), paper-repo (text).
3. `table_vs`: report the numbers as supplied. The text states that the without-description row coincides with the Qwen2-VL-7B-Instruct row of the Task-1 table (Qwen2.5-VL-7B there: F1 0.2349) and that the with/without comparison is internal to Task 3; no claim that description improves over the Task-1 Qwen2.5-VL-7B result. The caption names the model without asserting more than the source does. Claim kept: precision and F1 up, recall down, within Task 3.
4. Overview-only statements: 687 corrected / 1,222 new errors may appear once in the Task 3 text, worded as the authors' error-level count, never in the abstract or as a table value. Task 2 numbers are worded as read from the figures (approximate): zero-shot declines (~0.23 -> ~0.16), LoRA ~0.26 -> ~0.49, full fine-tuning ~0.24 -> ~0.51; the ">30 pp" is stated as the gap to zero-shot at the end of the period, not a gain over the start. User A: user-only LoRA above all-users LoRA mid-period, below it in the last weeks; the ~50 pp is relative to zero-shot; "eventually surpassing" is NOT claimed. Task-2 model "Qwen2.5-VL-3B" is attributed to the setup description, with no invented hyperparameters.
5. Writing constraints from AGENTS.md: a dedicated validation section; no Limitations / Future-work / Acknowledgements sections (what the benchmark does not measure goes in the Discussion/Conclusion); add `\graphicspath{{figures/}}` to the template; 6 pages double-column.

Update: figtab-repo kept `table_zn` steps 1 and 2 as separate rows (as supplied) with the -962 fix and a caption that states each step neutrally; accepted instead of the merged row in decision 2. The text (paper-repo) should still refer to the combined result of steps 1-2 as 11,285 images / 26,065 bboxes / 3,071 classes.
