# Derived quantities used in the paper (paper-repo, analysis)

Sources: `/initial-state/inputs/9/table_rr.tex` (72B), `table_le.tex` (7B), `table_im.tex` (ablation),
figures in `/initial-state/inputs/5/` (values read off the plots are approximate, marked ~).
Recomputed by hand from the table cells; no new experiments are possible (no GPUs, no checkpoints).

## Delta rows checked against the table entries
72B vs best open-source entry per column (table_rr):
| bench | ours | best open baseline | delta (recomputed) | delta in table |
|---|---|---|---|---|
| MathVista | 80.4 | 74.8 Qwen2.5-VL-72B | +5.6 | +5.6 |
| MathVerse | 63.5 | 57.2 Qwen2.5-VL-72B | +6.3 | +6.3 |
| MathVision | 44.9 | 38.4 Qwen2.5-VL-32B | **+6.5** | +6.8 (= vs Qwen2.5-VL-72B 38.1) |
| MMMU-Pro | 55.9 | 52.2 Llama4-Scout | +3.7 | +3.7 |
| MMMU | 68.8 | 70.3 QvQ-72B | **-1.5** | -1.4 |
| EMMA | 38.5 | 34.1 Qwen2.5-VL-72B | +4.4 | +4.4 |
| MEGA | 51.3 | 49.0 Qwen2.5-VL-72B | +2.3 | +2.3 |
MMMU 68.8 is bolded in the table but is not the best open-source value (QvQ 70.3, Llama4-Scout 69.4).

7B vs best baseline per column (table_le):
| bench | ours | best baseline | delta (recomputed) | delta in table |
|---|---|---|---|---|
| MathVista | 74.9 | 73.0 MM-Eureka-7B (Qwen) | **+1.9** | +4.7 (vs OpenVLThinker 70.2) |
| MathVerse | 54.2 | 50.3 MM-Eureka-7B (Qwen) | **+3.9** | +6.3 (vs OpenVLThinker 47.9) |
| MathVision | 32.3 | 29.9 R1-Onevision | +2.4 | +2.4 |
| MMMU-Pro | 41.7 | 37.3 OpenVLThinker | +4.4 | +4.4 |
| MMMU | 56.7 | 56.0 InternVL2.5-8B | +0.7 | +0.7 |
| EMMA | 29.7 | 26.6 OpenVLThinker | +3.1 | +3.1 |
| MEGA | 37.2 | 35.0 Qwen2.5-VL-7B | +2.2 | +2.2 |

Gains over the base model (RL effect): 7B vs Qwen2.5-VL-7B: +6.7, +7.9, +7.2, +4.8, +2.4, +8.2, +2.2.
72B vs Qwen2.5-VL-72B: +5.6, +6.3, +6.8, +4.3, +1.8, +4.4, +2.3. 32B vs Qwen2.5-VL-32B: +4.1, +8.4, +2.1, +1.1, +6.2, +6.8, +6.6.

## Ablation (table_im), mean over the 5 benchmarks
full 46.56; w/o FR 45.16; Filter (no SSR) 43.48; GRPO 42.66; no Text (13K) 45.18; no Science&Text (11K) 43.52.

## Figures (approximate readings)
- vanishing_adv: effective-query ratio ~0.41 -> ~0.20 over 15x16 steps; all-correct ~0.19 -> ~0.47; all-incorrect ~0.40 -> ~0.33.
- adv_histogram: GRPO ~0.37 of advantages in the bin at 0; Filter has no zero bin, mode ~0.18 just below 0; SSR spread, bimodal, mass concentrated at |A| ~ 0.3-0.8.
- ssr_eval_curve: val reward GRPO peaks ~0.429 at 11x16 steps then ~0.398 at 29x16; Filter ~0.436 max at 18x16 (run ends 23x16); SSR ~0.455 at 26x16, ~0.449 at 33x16.
- foret_ablation (printed values): VL-Reasoner-7B 29.75/72.35/53.13/40.94; forced at test time 30.49/72.90/53.56/41.15; bound 33.68/76.00/55.14/42.51; VL-Rethinker-7B 32.27/74.90/54.19/41.69 (MathVision/MathVista/MathVerse/MMMU-Pro). Rethinking ratio of VL-Rethinker ~36/~24/~78/~18 %.
  Note: VL-Reasoner MathVerse is 53.13 in the figure but 53.2 in table_im (w/o FR row).
