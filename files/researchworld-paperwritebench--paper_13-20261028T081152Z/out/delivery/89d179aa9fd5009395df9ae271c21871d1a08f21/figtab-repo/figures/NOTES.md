# Figure notes (presentation position)
All figures are the supplied JPEGs (`/initial-state/inputs/4`) except `ACM_task.jpg`, whose empty boxes were filled (see below).
No per-week data or plotting code was supplied, so the Task-2 curves and the histogram are not re-rendered.

## Suggested placement / width (6-page sigconf)
| File | Width | Claim it carries |
|---|---|---|
| ACM_task.jpg | figure* (page 2) | Overview of Tasks 1-3 (benchmark overview) |
| distribution_5.jpg | figure* | Traditional web datasets vs ours: source, imbalance, aesthetics, continuity, multi-dish |
| thumbnail_re.jpg, error_example.jpg | column / figure* (error_example is 3.5:1, needs figure*) | Data samples; typical erroneous raw records removed in curation |
| histogram_linear_pdf.jpg | column | Long-tailed class frequency (classes with >=10 samples; log x axis) |
| description_eg.jpg | column | Task 3 examples: one success and one failure of description-guided classification |
| all_data_1_35_with_legend.jpg | column | Task 2, all users |
| user_zero_lora_ma_wide_legend.jpg | column | Task 2, User A |

## ACM_task.jpg
Supplied version had empty boxes. Filled by `tools/fill_task_figure.py`: Task 1 "Class names" (text-encoder input), "Free-form description" (LMM output), "Predicted label"; Task 3 "Description of the whole meal image", "Predicted dish". Wording follows the supplied overview (description -> e5-large-v2 embedding -> highest cosine similarity; Task 3 describes the entire image, then classifies the crop).

## Values readable from the Task-2 curves (solid = weighted +-2-week moving average; read by eye/pixel, +-0.02, single runs, no CIs)
all_data_1_35_with_legend.jpg (x axis starts ~2023/05, ends ~2024/01; all users):
- Zero-shot: ~0.23 at the start, drifts down to ~0.095 (lowest, ~2023/12), ends ~0.16. So zero-shot does not improve with time (it gets worse as the label set drifts).
- Full fine-tune: ~0.24 -> ~0.51 at the end (~ +27 pp). LoRA: ~0.26 -> ~0.49 (~ +23 pp). Full FT is above LoRA for most of the period; the two meet around 2024/01 (~0.47).
- Weekly (dashed) values swing by roughly +-0.1, so only the moving averages support trend statements.
- The overview's ">30 pp" and "~20% -> >50%" are NOT supported by this figure (LoRA ~0.26 -> ~0.49); the figure also does not say which base model (overview: Qwen2.5-VL-3B).
user_zero_lora_ma_wide_legend.jpg (User A, ~2023/05 to ~2023/12):
- Zero-shot: ~0.135 at the start, ~0.05-0.11 afterwards, ~0.085 at the end.
- LoRA on all data: ~0.295 at the start, ~0.55 around 2023/10-11, ~0.65 at the end (peak ~0.69 just before).
- LoRA on User A only: ~0.17 at the start, rises to ~0.60-0.665 from ~2023/09 (~ +45-50 pp from the start to the peak at ~0.665), ends ~0.57.
- Crossover: user-only curve passes all-data at ~2023/07 (both ~0.38), stays above (~+0.05 to +0.10) until ~2023/11-12, then the curves meet (~0.60-0.62) and all-data is higher at the last points (0.65 vs 0.57). So "eventually surpassing all-users adaptation" holds for a mid-period, not at the end; weekly points of one user are noisy (several hit 0.0 or 0.8).
- x axis defects in the supplied image: the tick label "2023/10" appears twice; ticks are not evenly dated.
Histogram: x label says "Number of Images"; the supplied caption says "entries per class". Per the overview classes have >=10 samples after filtering; the largest class has ~1,700 entries (x ~ 1.7e3).
