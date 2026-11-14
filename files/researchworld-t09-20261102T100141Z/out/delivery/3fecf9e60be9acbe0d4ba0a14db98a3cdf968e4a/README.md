# paper-repo

Delivery root for the study "regression-based GATE estimation under network interference".

- `paper/` LaTeX source of the paper (NeurIPS 2026 template from `venue/`); `paper.pdf` is the PDF built from it.
- `venue/` template, checklist and format checker (venue-repo); `code/`, `results/` (experiment-repo); `figures/`, `tables/` (figtab-repo).

Build: `cd paper && TEXINPUTS=../venue: BIBINPUTS=.: latexmk -pdf main.tex && cp main.pdf ../paper.pdf`
Format check: `python3 venue/check_format.py paper.pdf paper/main.tex`

Numbers: every number quoted in the text is a macro in `paper/numbers.tex`, generated from `results/` by `python3 -I paper/scripts/make_numbers.py` (run from this directory) before building.
