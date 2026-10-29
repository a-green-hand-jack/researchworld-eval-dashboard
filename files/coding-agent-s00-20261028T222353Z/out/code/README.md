# Cover-time prediction on small graphs — reproduction

Layout: `code/` (experiments and analysis), `results/` (CSV, summary, table, figure), `paper/paper.tex` + `paper.pdf`.

Environment: Python 3.12 venv at `.venv` with numpy 2.4, networkx 3.6, matplotlib. Install with
`pip install numpy networkx matplotlib`. LaTeX: pdflatex with booktabs and microtype.

Commands (from `code/`):
```
python run_experiments.py --out ../results/cover.csv --walks 2000 --seed 1
python analyze.py
cd ../paper && pdflatex paper.tex && pdflatex paper.tex
```
Seeds: graph generation and walks both use `numpy.random.default_rng(1)` (and networkx seeds derived from it). The run takes about 10 s on one CPU core.

Note: the official ICML LaTeX template was not available offline; the paper uses the article class with an ICML-like layout.
