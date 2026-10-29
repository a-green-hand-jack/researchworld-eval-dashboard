# Review of paper-repo#9 (Version 1 into release), head aef7b4677f06f30573714f75fe4ee1bbcc969502

Inspected at that commit (clone of paper-repo, checked out at the head).

## Checked and supported
- Required paths: `template.tex` (164 lines, acmart sigconf nonacm kept, `\graphicspath{{figures/}}` present, no filecontents, no Acknowledgements/Limitations/Future-work sections), `references.bib` byte-identical to supplied input 5.
- Citations: all 37 cited keys exist in references.bib; no duplicate labels, every `\ref` resolves, every label is referenced. bibtex reports syntax errors only in supplied entries (not edited; the two uncited ones disclosed by paper-repo, plus stray commas before `abstract` fields that BibTeX recovers from); all 37 cited entries appear in the .bbl.
- Compile: acmart is not installable in my sandbox either (no network to CTAN), so I compiled a stand-in (extarticle 9pt, two columns, 7in text width) with the same body, tables and figures: no LaTeX errors, no undefined citations/references after bibtex + 2 passes. Real acmart build not verified by anyone.
- Numbers vs supplied material: tables table_kf, table_xj, table_vs, table_os match the supplied values (re-grouping/captions only; Delta row is arithmetic on supplied values); table_zn corrects a supplied arithmetic error (step 6 class change -982 -> -962 = 1,180-218), disclosed in figures/gen/README.md. Text numbers (11,460 -> 6,925 images, 14,349 boxes, 218 classes, 513 users, GPT-4o R@1 0.4243/F1 0.3732, CLIP R@5 0.6000, EVA 0.5944, Task-3 F1 0.159->0.230, P@1 0.102->0.179, R@1 0.366->0.324, 687/1,222, CLIP trace 81.70 vs 71.21, silhouette -0.021 vs 0.033) match.
- Figures opened: ACM_task.jpg (text filled into the empty boxes, consistent with the overview; unmodified original kept), distribution_5, error_example, histogram, all_data_1_35, user_zero_lora, description_eg are byte-identical to inputs except ACM_task. Task-2 readings in the text (zero-shot ~0.23->0.16; fine-tuning ~0.25->0.51/0.49; User A 0.17->~0.6, all-users better early and in the final weeks) agree with the plotted curves.
- Claims: hedged appropriately (single runs, one user, one model family, no IAA, single app, Task-3 baseline equals the Qwen2-VL-7B row), construction separated from findings, limitations in Discussion.

## Non-blocking findings (for the next version / final)
1. Length: in my stand-in the body (through Conclusion) runs to about 6.3 pages with references after; paper-repo reports the same. The objective asks for "a 6-page double-column paper". Real acmart may differ; trim ~0.4 page of body (e.g. shrink table*/figure* widths) or confirm references are outside the count before `final`.
2. The Task-2 figures cover roughly Jun 2023-Jan 2024 (all users) and May-Dec 2023 (User A) although the data span to Oct 2024; the text says "plotted period" but should state the evaluated period explicitly.
3. Task-2 protocol wording (train on accumulated logs, evaluate on the following period; "full fine-tuning" arm) is inferred from figures/overview; say so or keep hedged. Lack of code/ means LoRA/prompt details are not given; the text does not invent them (good).
4. `figures/fig_task1_recall.pdf`, `fig_task3_menu_effect.pdf`, `thumbnail_re.jpg` are delivered but unused; harmless.
5. Related-work sentence about personalization work being "evaluated on data collected from a food-logging application" rests on flg469/Aizawa2013 which I cannot verify from the bib; soften if unsure.

## Conclusion
Supported as a version for release; approved.
