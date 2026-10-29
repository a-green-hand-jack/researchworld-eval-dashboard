# Cover-time prediction on small graphs: reproduction

Environment: Python 3 (standard library only; no numpy/networkx). CPU only. About 1 minute per seed.

    cd code
    python3 -I exp.py --seed 0 --walks 2000 --out results.json
    python3 -I analyze.py results.json > analysis_seed0.txt
    python3 -I exp.py --seed 1 --walks 2000 --out results_s1.json
    python3 -I analyze.py results_s1.json > analysis_seed1.txt

Seeds: `random.Random(seed)` drives graph generation, start vertices, and walks.
`exp.py` writes per-graph mean cover time, 95% CI half-width, m, n, D, max degree, and 2m(n-1).
`analyze.py` fits the four log-linear models and prints leave-one-family-out APE; it writes `cv_summary.json`.

Paper: `paper/main.tex` (ICML 2026 style files included). Build with `latexmk -pdf main.tex`.
