# Cover-time prediction on small graphs — reproduction notes

## Deliverables
- `paper/main.tex`, `paper/main.pdf` — 3-page short paper (ICLR 2026 style, built from the official ICLR Master-Template `iclr2026` files; `.sty/.bst` copied into `paper/`).
- `paper/refs.bib` — references (Aleliunas et al. 1979; Feige 1995; Lovász 1993).
- `code/cover.py` — graph generation, Monte Carlo cover-time simulation, exact validation for n ≤ 8.
- `code/analyze.py` — predictors, repeated 5-fold CV, leave-one-family-out, bootstrap CIs, figure.
- `results/graphs.csv` — per-graph n, m, Δ, D, MC mean, SE, 95% CI, exact value (n ≤ 8).
- `results/summary.md` — all tables quoted in the paper (including per-family LOFO errors).
- `results/fig_predictions.pdf`, `results/run_log.txt`.

## Environment
- Python 3, numpy 2.4.6 (no networkx needed). matplotlib optional (for the figure).
- pdflatex / bibtex (TeX Live 2025).
- CPU only; full run takes a few minutes on one core.

## Commands
```
python3 code/cover.py --walks 2000 --seed 0 --out results/graphs.csv > results/run_log.txt
python3 code/analyze.py --csv results/graphs.csv --out results/
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

## Seeds
- Graph generation (random trees, random regular, G(n,p)): `build_graphs(seed=0)` → `np.random.default_rng(0)`.
- Monte Carlo walks: `np.random.default_rng(1000 + seed)` with seed 0, 2000 walks per graph, start vertex uniform.
- CV splits: `np.random.default_rng(0)` (20 repeats, 5 folds); bootstrap: `np.random.default_rng(1)`.

## Notes
- No external data or downloads were used for the experiments. The ICLR template was fetched from the official ICLR Master-Template repository on GitHub.
- The exact values (n ≤ 8) are computed by solving the linear system over (vertex, visited-set) states.
- Limitations are discussed in §Discussion of the paper (synthetic sample of 236 graphs, uniform start vertex, one generator seed).
