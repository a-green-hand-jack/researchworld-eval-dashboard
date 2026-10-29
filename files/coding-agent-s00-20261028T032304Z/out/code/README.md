# Cover-time prediction on small graphs — reproduction

Environment: Python 3 with numpy, networkx (3.x), matplotlib in `/work/.venv` (CPU only, ~15 s total).

    cd /work/code
    /work/.venv/bin/python cover.py --walks 10000 --seed 0 --out ../results/cover.csv
    /work/.venv/bin/python analyze.py

- `cover.py`: builds 140 connected graphs (6 <= n <= 30, 15 families) with `--seed` for random generators and estimates cover time from a uniform random start using `--walks` independent walks (vectorised). Simulator validated on C10 and K10 against exact values.
- `analyze.py`: fits the bound-only, (n,m), (n,m,diam), (n,m,diam,dmax) predictors; leave-one-family-out evaluation with bootstrap CI; writes `results/summary.txt`, `results/lofo_by_family.csv`, `figs/*.pdf`.
- Paper: `paper/main.tex` (ICML 2026 style), compiled to `paper/paper.pdf`.
- Seeds: graph generation seed 0 (rng = default_rng(0), walks rng = default_rng(1)); bootstrap rng default_rng(0).
