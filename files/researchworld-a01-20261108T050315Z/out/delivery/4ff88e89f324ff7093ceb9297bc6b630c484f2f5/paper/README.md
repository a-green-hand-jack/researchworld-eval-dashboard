Paper sources (NeurIPS 2026 main track, official template unmodified; no author information).
- `main.tex` inputs `sections/{intro,related,method,experiments,discussion,appendix}.tex` and `checklist.tex`; `references.bib` is the checked bibliography from idea-repo.
- `main.pdf` is the build of the current `main`: `cd paper && latexmk -pdf main.tex`.
- Figures and tables are read from `../figures` (figtab-repo) and are not copied; every number in the text comes from `../code/results` or `../figures/tables`.
- Check: `python3 -I venue/check_pdf.py paper/main.pdf paper/main.tex paper/sections/*.tex --sty paper/neurips_2026.sty` (the four WARNs say that the template is loaded in `main.tex`, not in the section files).
