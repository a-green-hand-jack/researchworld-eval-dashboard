# figtab-repo (presentation)

- `figtab/results.csv`: every number of the experimental log used in a table/figure (transcribed by hand; gap rows are recomputed and asserted equal to the logged gaps by the generator).
- `figtab/make_figures.py`: renders `figures/fig_ablation_gaps.{pdf,png}` and `tables/*.tex` (full `table` environments with captions and labels `tab:baselines`, `tab:mixed`, `tab:ablations`; figure label is chosen by the paper). Run from the repo root.
- Gap definitions: |Retrained − Unlearned(−)| everywhere except `tab_mixed_linear.tex`, where |Δ| is Unlearned(+) vs Unlearned(−), as in the log.
- All numbers are single runs; no error bars exist in the log and none are drawn.
