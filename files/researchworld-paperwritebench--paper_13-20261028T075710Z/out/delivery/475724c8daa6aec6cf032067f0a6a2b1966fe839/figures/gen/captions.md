# Caption facts for the unmodified figures (only what the figure itself shows)

- `all_data_1_35_with_legend.jpg`: weekly accuracy (y, 0-1) vs. date (x, 2023/05-2024/01-ish); Zero-shot, LoRA, full fine-tuning, each trained incrementally on all users' data up to the previous week; dashed = per-week values, solid = weighted moving average (weights proportional to weekly volume, +-2 weeks). Per-week n and run-to-run variability are not given: say "single run" only if the analysis owner confirms.
- `user_zero_lora_ma_wide_legend.jpg`: same for one heavy logger ("User A"); LoRA on that user's data vs. LoRA on all users vs. zero-shot. Duplicate x tick label "2023/10" in the image.
- `histogram_linear_pdf.jpg`: x = images per class (log), y = number of dish types (linear); arrows mark classes with illustrative examples (shown in the original paper figure, not in this file).
- `distribution_5.jpg`: conceptual comparison (no data).
- `thumbnail_re.jpg`, `description_eg.jpg`, `error_example.jpg`: examples.
