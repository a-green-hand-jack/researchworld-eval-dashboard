# Discrepancies in the supplied material (see wiki `Brief` for full context)

1. `tables/table_vs.tex` "w/o description" row (F1 0.1594, R@1 0.3656, R@3 0.4590, R@5 0.4781) is identical to the Qwen2-VL-7B-Instruct row of `tables/table_kf.tex`; its caption says Qwen2.5-VL-7B-Instruct, whose table_kf row is 0.2349/0.3684/0.4609/0.4859. Cannot be resolved from supplied material; the paper must not assert either reading as fact without a caveat.
2. Overview "eventually surpassing all-users adaptation" (User A): `figures/user_zero_lora_ma_wide_legend.jpg` shows user-only LoRA above all-data LoRA from ~July to ~Nov 2023, but all-data LoRA (~0.65) is above user-only (~0.57) in the final weeks.
3. Overview "from ~20% to >50%, >30 pp": `figures/all_data_1_35_with_legend.jpg` LoRA ends ~0.49 (full fine-tune ~0.51); zero-shot falls ~0.23 -> ~0.16, so the ~33 pp gap is relative to zero-shot at the end.
4. `table_os`: FoodLogAthl-218 "#samples" 14,349 counts bounding boxes (6,925 images); other rows count images.
5. User A figure: x tick label "2023/10" appears twice; single user, noisy weekly points.
6. No `code/` directory was supplied; training/eval hyper-parameters, splits, prompts are not available.
7. 687 corrected / 1,222 new errors (Task 3) appears only in the overview text.
8. Bib: `li2024llava` is LLaVA-Med, not LLaVA (use `liu2024visual`/`liu2024improved`); no Qwen2-VL/Qwen2.5-VL/LLaVA-OneVision/GPT-4o-specific entries (`bai2023qwen`, `achiam2023gpt` are the nearest).

See wiki `Brief` sections 7-8 for which overview numbers are table/figure-backed vs text-only, and the handling recommended for the Task 3 baseline row.
