# Review record: paper-repo PR #8 (Version 1 -> release), head 9c493f45cdb5b28d6240b0780075d725a32c72cc

Inspected at that commit: template.tex, references.bib, 8 figures, 5 tables, CODEOWNERS; status hutian/delivery = success.

## Checked and supported
- references.bib byte-identical to the supplied file; all 46 cited keys exist; no duplicate labels, all \ref resolve.
- Tables vs /initial-state/inputs/8: all numbers identical except table_zn step 6 class diff (source -982, delivered -962 = 1,180-218; the correct arithmetic, disclosed) and added deltas in table_vs (arithmetically correct: +0.0710, +0.0769, -0.0416, -0.0558, -0.0445). table_os row for FoodLogAthl-218 matches source (218 / 14,349).
- Text numbers match tables: pipeline counts, 0.4243/0.3732/0.4991/0.6000, CLIP trace 81.70 vs 71.21, Silhouette -0.0210 vs 0.0335, 687/1,222, F1 0.1594->0.2304, P@1 0.1019->0.1788, R@1 0.3656->0.3240. All four cluster indices do agree in direction for all three extractors (verified by hand).
- Task 2 read-offs (zero-shot ~0.23 -> ~0.16; FT ~0.24 -> ~0.5; User A zero-shot 0.07-0.14, user LoRA ~0.6 vs all-users 0.4-0.55, all-users 0.65 vs 0.57 at the end) agree with the figures I opened. Marked approximate; ">50%" LoRA claim from the overview was correctly NOT repeated (LoRA ~0.49).
- Honest disclosures present: no inter-annotator agreement, table_vs baseline row == Qwen2-VL-7B row of table_kf, single runs, no CIs, F1 averaging / splits / prompts not available, CLIP-filter bias, single source, Japanese-style meals.
- All 8 figures opened: all render, legible, non-blank. ACM_task.jpg has its empty boxes filled by figtab (generator script delivered, disclosed).
- Structure follows the benchmark-paper guidance (no Method section, validation section, no Limitations/Future-work/Acknowledgements sections, no filecontents, \graphicspath kept).
- Stand-in build (acmart unavailable offline, extarticle two-column 9pt): compiles, 7 pages = ~6 body + references, no undefined refs/overfull boxes. acmart layout itself NOT verified by me either.

## Open findings (request changes)
1. figures/user_zero_lora_ma_wide_legend.jpg (Fig. 7): the x axis has the tick label "2023/10" twice (between 09 and 11), so month positions after September are ambiguous. The text uses "July to August", "autumn" for this figure. Caption/text must say the axis labels are duplicated in the supplied figure and month claims are approximate (or avoid month claims for this figure); figtab to say whether it can be corrected from supplied material.
2. figures/histogram_linear_pdf.jpg (Fig. 5) caption says "arrows mark illustrative classes" but the delivered image has unlabeled arrows and no examples; the claim is not checkable. Reword (arrows are unlabeled in the supplied figure) or drop.
3. AGENTS.md: the benchmark overview figure goes on page 2. In my stand-in Fig. 1 (tasks) lands on page 1 and Fig. 2 (distribution_5, figure*) on page 3. Place the overview so it falls on page 2 in the acmart build (e.g. move the figure* environment earlier in the Introduction so it floats to the top of page 2).
4. Minor: Task 2 text states LoRA experiments use Qwen2.5-VL-3B but not the base model of the full fine-tuning curve (nor of the User-A adapter); say it is not stated in the material. llava-onevision-qwen2-7b-ov row has no citation.
5. Not blocking: Related Work leaves unused relevant bib entries (e.g. kaur2019foodx, farinella2014benchmark, wu2021large, qiu2022mining, merler2016snap); one more sentence on Task-2-style continual/personal benchmarks would strengthen the positioning.

Conclusion at this head: changes requested (1-4); 5 is advisory.

---
# Re-review at head 409d85759c5e355727e641e4b42bc6f9663b35a1 (hutian/delivery = success)
Diff from 9c493f4 is template.tex only. Findings: (1) Fig. 7 duplicate tick now stated in the text, month claims softened ("middle of the period", "several months") -- resolved; figtab confirmed the axis cannot be corrected from the supplied material. (2) Fig. 5 caption now says the arrows are unlabeled in the supplied figure -- resolved. (3) Overview figure: the task figure now lands on page 2 in my stand-in build -- resolved as far as I can check without acmart. (4) Base models of full fine-tuning and User-A adapter stated as not given; llava-onevision folded into the LLaVA-family citation -- resolved. (5) Related Work now uses kaur2019foodx, farinella2014benchmark, wu2021large, merler2016snap and positions Task 2 -- done.
Rebuilt (stand-in two-column class): compiles, no undefined refs/overfull, all cited keys in references.bib, body ends on page 6, references follow. Numbers unchanged from the checked version. Not verified: the real acmart layout and page count (class unavailable offline); residual risk accepted and disclosed by paper-repo.
Conclusion: approved.

---
# Re-review at head 002e42c4c2d3ad3aa4d493001cfc06d60b6ffc35 (hutian/delivery = success)
Diff from 409d857: two caption edits in template.tex only (Fig. 5 arrows "mark classes of different sizes (unlabeled in the source figure)"; Fig. 7 caption states ticks are every four weeks, month-labeled, so 2023/10 appears twice). Both match figtab's read of the figures and what I saw. No change to numbers, labels, citations or floats. Approved.

---
# Final: paper-repo PR #14 (main -> final), head 002e42c4c2d3ad3aa4d493001cfc06d60b6ffc35
Head is the identical commit reviewed and approved for PR #8; hutian/delivery = success; template.tex, references.bib (nonempty, byte-identical to supplied), 8 figures and 5 tables present. All open findings closed; residual risk: real acmart layout/page count unverified (disclosed). Approved.
