# Cover-time prediction on small graphs — reproduction

Paper: `paper/paper.pdf` (source `paper/paper.tex`, bibliography `paper/refs.bib`, ICML 2026 style files in `paper/`).

## Environment
- Python 3.11.2, NumPy, NetworkX, Matplotlib (virtualenv at `/work/.venv`).
  `python3 -m venv .venv && .venv/bin/pip install numpy networkx matplotlib pypdf`
- LaTeX: pdflatex + bibtex (TeX Live 2022).

## Commands (CPU only, ~20 s total)
```
cd code
../.venv/bin/python run_experiments.py   # -> results/graphs.csv, results/validation.csv
../.venv/bin/python analyze.py           # -> results/results.md, paper/fig_main.pdf
cd ../paper && pdflatex paper.tex && bibtex paper && pdflatex paper.tex && pdflatex paper.tex
```

## Files
- `code/cover.py` — graph families, vectorised SRW Monte Carlo, exact DP cover time (n ≤ 9), hitting times, Matthews bound.
- `code/run_experiments.py` — builds 377 graphs, estimates start-averaged cover times, validates against exact values.
- `code/analyze.py` — LOFO and 10-fold CV evaluation of predictors, bootstrap CIs, per-family tables, figure.

## Seeds
- Graph generation: `make_graphs(seed=0, per_family=30)` (NumPy `default_rng(0)`).
- Simulation: `default_rng(12345)`, 100 walks per start vertex.
- CV: repeats use `default_rng(rep)` for rep = 0..19. Bootstrap: seed 0.
