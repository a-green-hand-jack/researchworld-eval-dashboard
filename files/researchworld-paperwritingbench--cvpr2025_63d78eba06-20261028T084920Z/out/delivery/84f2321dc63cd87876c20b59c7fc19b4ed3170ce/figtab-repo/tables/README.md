# Tables and figures: claim map (figtab-repo)

All numbers come from `tables/data/log_results.csv` (transcribed from the experimental log); `tables/code/make_tables.py`
regenerates every file here and `python3 tables/code/common.py` recomputes each logged
"Performance Gap" from the raw rows (0 mismatches). Tables use `booktabs` and `\cref`; they add no packages
(no `multirow`). Units: % accuracy / MIA score; gaps in percentage points.

| Label | File | Claim it lets a reader check | Log rows |
|---|---|---|---|
| `tab:baselines` | `tab_baselines.tex` | Unlearned(-) keeps utility (70/71/68) where NegGrad, Random Labels, JiT, Adversarial fall to 52 or 21; MIA: Adversarial is closest to 50 (50.0), Unlearned(-) 51.4 | Comparative analysis |
| `tab:mixed` | `tab_mixed.tex` | On CIFAR-100 mixed-linear ResNet-18, Unlearned(-) is within 0.1-0.5 test points of Unlearned(+) (the logged gap), and 0.9-2.2 below Retrained; remaining accuracy differs from Unlearned(+) by 2.2-6.6 (above at 20/15%, below at 10%) | Mixed linear networks |
| `tab:forget_size`, `tab:perturb`, `tab:lambda` (or the combined `tab:ablations`) | `tab_*.tex` | gap to Retrained grows with forget size (0 -> 2 -> 14 test pts), shrinks with perturbations (15 -> 2 -> 0) and with lambda (2 -> 1 -> 0) | three ablations |
| `fig:main_datasets` | `figure_1_caption.tex` | Unlearned(-) ~ Unlearned(+) on four datasets (supplied figure) | Observation 1, figure_1.png |

Every table is also available as a float-free `tabular_<name>.tex` (a braced group, `\footnotesize`, `\input{tables/tabular_<name>}`); `tab_<name>.tex` is the float using it. Use either the three ablation tables or the combined one, not both.

Figure 1 legibility: the supplied PNG is 864 px wide, so its in-image text is ~4-5 pt even at 7 in; place it as `figure*` at `\linewidth`. Bars are separated by colour and by fixed left-to-right order, stated in the caption (no hatches: the image is supplied and its bar values outside CIFAR-10 are not logged, so it is not re-rendered).

Suggested placement under the 8-page limit: main text `fig:main_datasets` (the only figure), `tab:baselines`, `tab:mixed`, `tab:forget_size`;
`tab:perturb`, `tab:lambda` (or the combined `tab:ablations`) in main text if the 8 pages hold, else in the appendix.

## Things the text must not overstate
- Mixed-linear logged gaps are to Unlearned(+), not Retrained (to Retrained: test 0.9-2.2 below, remaining -1.9 to +4.3).
- 10% forget row, 500-perturbation row and lambda=0 row are one configuration.
- 15% forget (14-15 pt loss) and 250 perturbations (15-16 pt) are failures of the method, not noise; reported as is.
- Lambda effect (2/1/0 pts) and 1000-perturbation effect (0-1 pts) are single runs with 1-point differences: "reduces" is what the log shows, not significance.
- Figure 1: CIFAR-100/Dogs/Caltech256 bar values are not in the log; do not quote them as numbers; the model behind the figure is not stated, do not call it mixed-linear.
- Unlearned(-) is not best on MIA closeness to 50 in `tab:baselines` (Adversarial 50.0).
