# Cover-time prediction on small graphs — reproduction

Layout: `code/` (simulator + experiment + analysis), `results/` (data.csv, summary.json,
family_table.md, fig_pred.pdf), `paper/` (paper.tex, paper.pdf, refs.bib; ICML 2026 style files from the official template).

## Environment
- Python 3.11, packages: numpy, pandas, networkx, matplotlib, tabulate
- gcc (for the C Monte Carlo simulator)
- CPU only; the full run takes ~30 s on 40 cores.

## Commands (run from `code/`)
    gcc -O2 -o cover cover.c -lm
    python run_experiments.py 5000 0    # master seed 0, 5000 walks per start vertex
    python analyze.py                   # RNG seed 12345 for CV/bootstrap
    cd ../paper && pdflatex paper.tex && bibtex paper && pdflatex paper.tex && pdflatex paper.tex

## Seeds
- Graph generation: `random.Random(0)` (master seed), plus networkx seeds drawn from it.
- Simulator: seed `100000*0 + i + 1` for graph index i (0-based); xorshift128+ PRNG.
- Analysis: `numpy.random.default_rng(12345)`.
