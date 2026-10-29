# Cover-time prediction on small graphs — reproduction

Paper: `paper/paper.pdf` (source `paper/paper.tex`, bibliography `paper/refs.bib`, ICML 2025 style files from the official `icml2025.zip`).

## Environment
- Python 3 standard library only (no numpy/networkx/matplotlib needed).
- LaTeX: pdflatex + bibtex.

## Commands
    cd /work/code
    python3 -I cover.py --out /work/results       --seed 2026 --trials 1000   # main run
    python3 -I cover.py --out /work/results_seed7 --seed 7    --trials 1000   # replicate
    cd /work/paper && pdflatex paper && bibtex paper && pdflatex paper && pdflatex paper

## Outputs
- `results/graphs.csv`: 195 graphs; n, m, avg_deg, max_deg, diam, 2m(n-1), Monte Carlo mean cover time (`cover`) and its standard error (`se`).
- `results/report.json`: OLS coefficients (log-space) and cross-validated error summaries.
- `results/stdout.txt`: console output of the main run.

## Seeds and randomness
Graph generation uses `random.Random(seed)`; each graph's walks use `random.Random(seed*100003 + index)`. Runtime is about 2 s per run on one CPU core.
