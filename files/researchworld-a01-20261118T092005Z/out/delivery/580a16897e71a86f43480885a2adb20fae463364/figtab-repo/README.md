# figtab-repo

Figures and tables of the paper (role `figtab-repo`).

- `DATA_CONTRACT.md`: the result-file schema the scripts read (from `experiment-repo`).
- `FIGURES.md`: per figure/table: claim, what it must show, how it is drawn, what it needs.
- `figtab/style.py`: shared style; sizes come from `venue.json` (venue's type size/widths).
- `figtab/make_*.py`: one script per figure/table; each writes a PDF (figures) or a `.tex` (tables) and a `.provenance.json` naming the input files and their checksums.

Inputs: `results/` of the delivery root. Outputs: `figures/figN_<name>.pdf`, `tables/tableN_<name>.tex` in the delivery root (`paper-repo` `dev`).
