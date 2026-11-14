# paper-repo

Delivery root. `paper/main.tex` (NeurIPS 2026 template, unmodified `neurips_2026.sty`), `paper/refs.bib`, built `paper/main.pdf`.
Figures/tables come from `figures/` and `tables/` (figtab position); code, data and results from `code/`, `data/`, `results/`; `REPRODUCE.md` from the analysis position.
Build: `cd paper && latexmk -pdf main.tex`.
Supplement: `paper/supplement_code.zip` (anonymised code, derived data and results; built by `python3 paper/make_supplement.py`). Version status: see the releases of `world/result`.
