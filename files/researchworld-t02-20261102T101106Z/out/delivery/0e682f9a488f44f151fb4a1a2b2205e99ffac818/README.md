# Width and delayed generalization on modular arithmetic

Deliverables (paper-repo):
- `paper/main.pdf` — the paper (NeurIPS 2026 template, anonymous); LaTeX source `paper/main.tex`, `paper/references.bib`, checklist `paper/checklist.tex`. Build: `cd paper && latexmk -pdf main.tex`.
- `paper/REPRODUCE.md` — reproduction document: environment, data, seeds, commands and run times, table/figure to script map, provenance, unfinished runs, withheld-paper exposure.
- `experiments/` — trainer (`grok.py`), sweeps (`sweep.py`), analyses; run logs in `experiments/runs/`.
- `results/` — aggregated CSV/JSON used by the paper.
- `figures/` — figure and table generators (`figures/src/`) and outputs.
- `venue/` — venue rules and the unmodified template.
