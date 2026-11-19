# Predicting full-benchmark LLM accuracy from a few items

Layout of the delivery (owners in `.forgejo/CODEOWNERS`):

| path | content |
|---|---|
| `paper.pdf`, `paper/paper.pdf` | the paper (NeurIPS 2026 main track template, anonymous mode) with its checklist |
| `paper/` | LaTeX source (`main.tex`, `sections/`, `refs.bib`, `paper_checklist.tex`), `build.sh`, `make_tables.py` (tables built from `figures/` and `results/`) |
| `code/`, `results/`, `REPRODUCE.md` | analysis code, per-prediction results and tables, reproduction guide (environment, pinned data, seeds, commands, run times) |
| `figures/` | figure and table generators and their outputs |
| `venue/` | venue specification, unmodified official template, format checker |

Rebuild the paper: `sh paper/build.sh` (needs pdflatex and bibtex; uses the official style in `venue/template/`). Check the format: `python3 -I venue/check_format.py paper.pdf`. Tables of the main text: `cd paper && python3 -I make_tables.py`; figures: see `figures/README.md`.
