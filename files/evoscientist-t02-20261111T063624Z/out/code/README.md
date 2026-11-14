# Width and delayed generalisation on modular arithmetic

* `paper/main.pdf` (+ LaTeX source `paper/main.tex`, `appendix.tex`, `checklist.tex`, `refs.bib`, `figs/`, `tables/`): NeurIPS-2025-template paper with the NeurIPS checklist.
* `code/`: all code (`grok.py` models/training, `experiments.py` sweeps, `sweep.py` runner, `analysis.py` figures/tables/numbers),
  `PREREG.md` (predictions written before the main sweeps), and `README.md` (environment, seeds, commands, run times, figure/table map).
* `results/`: one JSONL file per experiment (every run incl. full curves) and `summary.json` (all numbers quoted in the paper).
* `code/logs/`: sweep logs, reference check, compute statistics.

Rebuild: `cd code && python analysis.py && cd ../paper && python make_checklist.py && latexmk -pdf main.tex`.
