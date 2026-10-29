# figtab generators
- `prepare_figures.py [SRC DST]`: builds `figures/` from `/initial-state/inputs/4` (fills the empty boxes of `ACM_task.jpg` with generic role labels; other figures copied, capped at 2000 px width).
- `preview.tex`: width check of `tables/` and `figures/` with a surrogate two-column geometry (acmart is not installed in the sandbox; column 241 pt, text 506 pt). Build: `latexmk -pdf -output-directory=/tmp/pvbuild preview.tex` after copying the tables (strip `\cite`).
- `tables/*.tex` are hand-typeset from the supplied `/initial-state/inputs/8/*.tex`; numbers unchanged (only $\Delta$ row of `table_vs` is derived).
