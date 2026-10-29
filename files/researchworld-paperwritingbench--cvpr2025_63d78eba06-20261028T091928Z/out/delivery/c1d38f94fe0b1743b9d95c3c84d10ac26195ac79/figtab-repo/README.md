# figtab-repo: figures and tables

- `data/log_results.csv`: every number, hand-transcribed from the experimental log (INSTRUCTIONS.md, "2. Raw Numeric Data").
- `code/make_all.py`: regenerates everything below (`python3 code/make_all.py`); asserts logged gap rows match recomputed differences.
- `figures/fig_ablations.pdf` (+ `.png` preview): gap to Retrained vs forget size / perturbations / lambda.
- `tables/*.tex`: `\input`-ready snippets with caption and label: `tab:baselines`, `tab:mixed`, `tab:ablations`, `fig:ablations` (figure* wrapper).
- `figures/figure_1.png`: byte-identical copy of the supplied input (864x568 px; not regenerated, only CIFAR-10 values are traceable to the log).

Labels use `\cref`. Tested with cvpr.sty: widths fit a column (tables) / full width (figure*).
