# paper-repo

Delivery root. `paper/main.tex` (NeurIPS 2026 template, unmodified `neurips_2026.sty`), `paper/refs.bib`, built `paper/main.pdf`.
Figures/tables come from `figures/` and `tables/` (figtab position); code, data and results from `code/`, `data/`, `results/`; `REPRODUCE.md` from the analysis position.
Build: `cd paper && latexmk -pdf main.tex`.
Status: complete draft for review; the built PDF on `main` is rebuilt with every merged change.

PDF build note: the template uses T1 fonts; without the `cm-super` Type 1 fonts TeX falls back to bitmap (Type 3) fonts, which the
template says are rejected. Install `cm-super` (CTAN `fonts/ps-type1/cm-super.zip`) into `TEXMFHOME`, run `texhash` and
`updmap-user --enable Map=cm-super-t1.map --enable Map=cm-super-ts1.map`, rebuild, and check that `pdffonts paper/main.pdf | grep -c "Type 3"` prints 0.
