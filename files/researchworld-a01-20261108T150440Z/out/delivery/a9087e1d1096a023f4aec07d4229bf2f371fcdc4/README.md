# paper-repo

Delivery root. `paper/main.tex` (NeurIPS 2026 template, unmodified `neurips_2026.sty`), `paper/refs.bib`, built `paper/main.pdf`.
Figures/tables come from `figures/` and `tables/` (figtab position); code, data and results from `code/`, `data/`, `results/`; `REPRODUCE.md` from the analysis position.
Build: `cd paper && latexmk -pdf main.tex`.
Status: draft with analysis delivery 2 and the T5/T6 tables integrated; revised after the first internal review of the pull request into final; only the OLLB top-500 Copeland slice is pending (declared in the limitations); not yet a released version.
