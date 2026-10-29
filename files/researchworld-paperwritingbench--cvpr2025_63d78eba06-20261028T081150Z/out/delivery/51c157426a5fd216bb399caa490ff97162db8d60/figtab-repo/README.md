# figtab-repo: figures and tables

Delivered paths (copied into `paper-repo`): `figures/`, `tables/`, `figtab_src/`.

| item | file | label | source |
|---|---|---|---|
| Fig. (supplied, unchanged) | `figures/figure_1.png`, caption `figures/figure_1_caption.txt` | - | `/initial-state/inputs/2` |
| Gap vs ablation axes | `figures/gap_ablations.{pdf,png}`, caption `figures/gap_ablations_caption.txt` | `fig:gap` (caption cites `tab:forget_size`, `tab:ablations`) | `figtab_src/make_gap_figure.py` |
| Forget-size ablation | `tables/forget_size.tex` | `tab:forget_size` | `figtab_src/make_tables.py` |
| Perturbation + lambda ablations | `tables/ablations.tex` | `tab:ablations` | same |
| Mixed linear network | `tables/mixed_linear.tex` | `tab:mixed` | same |
| Source-free baselines | `tables/baselines.tex` | `tab:baselines` | same |

All numbers are transcribed in `figtab_src/data.py` from the experimental log (single runs; no seeds reported, hence no error bars).
Regenerate: `python3 figtab_src/make_tables.py; python3 figtab_src/make_gap_figure.py`.
Tables are single-column booktabs fragments using only template packages (`\input{tables/...}`). Check: compiled with the supplied cvpr template, no warnings.
Gap = absolute difference in percentage points to Retrained; `tab:mixed` also gives the gap to Unlearned(+), the reference used in the log for that table.
Space: `tab:mixed` is the tallest (15 rows); move it to the appendix first if the 8-page limit binds.

Note for the text of Fig. 1 (supplied figure): the log has no numbers for its CIFAR-100/Stanford Dogs/Caltech-256 panels. Describe them qualitatively only; per `experiment-repo` (`analysis/FINDINGS.md`, `fig1_gaps.csv`, pixel-read, +/-1 pt) Unlearned($-$) tracks Unlearned($+$) within about 3 points there, but both lie 4-7 points below Retrained on test and forget accuracy. Values were verified against `experiment-repo` `analysis/results_ledger.csv` and `gap_check.csv` (all table entries and gaps agree).
