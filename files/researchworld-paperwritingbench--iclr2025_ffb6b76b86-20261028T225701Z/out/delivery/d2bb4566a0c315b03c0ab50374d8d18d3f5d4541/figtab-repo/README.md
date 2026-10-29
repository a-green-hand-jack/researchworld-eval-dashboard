# figtab-repo — presentation

Delivered (to `paper-repo`):
- `tables/table_1.tex` … `table_4.tex`: complete `table` environments (labels `tab:fim`, `tab:general`, `tab:code`, `tab:beam`). Need `\usepackage{booktabs}` in the preamble. Include with `\input{tables/table_N}`.
- `figures/fig_deltas.pdf`: two-panel figure (a) byte − token score per model/benchmark (Tables 2–3), (b) top-2 ensemble − best single model. Width 5.5 in; use `\includegraphics[width=\linewidth]`.
- `figures/gen/`: `data.py` (numbers transcribed from the experimental log), `make_tables.py`, `make_delta_figure.py`. Run both scripts to regenerate.



`figures/figure_1..6.png` are the supplied files, unmodified; `figures/NOTES.md` records what each shows, its legibility, and a suggested width.
