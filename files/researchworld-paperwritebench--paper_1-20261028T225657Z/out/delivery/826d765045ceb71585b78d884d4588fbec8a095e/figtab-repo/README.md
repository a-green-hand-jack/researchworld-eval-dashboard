# figtab-repo — figures and tables of the VL-Rethinker paper

Delivered into `paper-repo` as `figures/` and `tables/` (floats to `\input`, see labels below).

| File | Label | Source | Claim it supports |
|---|---|---|---|
| `figures/fig_teaser.tex` | `fig:teaser` | `inputs/5/teaser-2.jpg` | 72B vs proprietary models |
| `figures/fig_overview.tex` | `fig:overview` | `inputs/3/assets/overview-2.pdf` (vector) | method pipeline (SSR, Forced Rethinking) |
| `figures/fig_vanishing_adv.tex` | `fig:vanishing_adv` | `inputs/5/vanishing_adv.jpg` | effective-query share collapses in GRPO |
| `figures/fig_rethinking.tex` | `fig:rethinking` | `inputs/5/rethinking.jpg` | example self-correction plus a word cloud of rethinking phrases |
| `figures/fig_training_dynamics.tex` | `fig:training_dynamics` (`fig:ssr_eval_curve`, `fig:adv_histogram`) | `inputs/5/ssr_eval_curve.jpg`, `adv_histogram.jpg` | SSR stabilises training and moves advantages away from 0 |
| `figures/fig_foret_ablation.tex` | `fig:foret_ablation` | `inputs/5/foret_ablation.jpg` | training-time rethinking beats test-time forcing; selective rethinking |
| `tables/table_rr.tex` | `table:main_results` | `inputs/9/table_rr.tex` | 72B SoTA among open models |
| `tables/table_le.tex` | `table:7b_results` | `inputs/9/table_le.tex` | 7B SoTA among similar-size models |
| `tables/table_im.tex` | `table:ablation_results` | `inputs/9/table_im.tex` | SSR, Forced Rethinking and data-mix ablation |

Table entries are copied unchanged. The derived marks (bold, underline, Δ) are recomputed by `scripts/check_tables.py`, which corrects four Δ values of the supplied tables (see issue #2). `preview/preview.tex` renders every float in a two-column layout for inspection.

Needs in the paper preamble: `graphicx`, `subcaption`, `booktabs`, `pifont`, `xcolor` with `table`, and `\model`. The supplied template already loads all of them. Every path is written as `figures/...` and is relative to the repository root.
