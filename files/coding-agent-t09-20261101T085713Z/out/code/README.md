# Regression-based GATE estimation under network interference — code & reproduction

Everything in the paper (tables, figures, numbers) is produced by the scripts below from simulations run in this repository.

## Layout
- `code/gate/` — library: `graphs.py` (loading/generation, Louvain clusters, edge corruption), `core.py` (population/outcome mechanisms, designs, estimators), `sim.py` (Monte-Carlo engine).
- `code/experiments.py` — definitions of experiments `e1_var … e10_clusterres` (+ `e0_smoke`). `python experiments.py <name> [R]` runs one and writes `results/<name>.csv.gz` (one row per replicate × estimator).
- `code/run_all.sh` — runs e1…e9 sequentially (`e10_clusterres` was run separately afterwards with `python experiments.py e10_clusterres`).
- `code/fig_*.py`, `code/tab_*.py`, `code/analysis_common.py` — figures/tables (outputs in `figs/`, `paper/tables/`, `results/summary_*.csv`).
- `paper/` — LaTeX source (ICML 2026 template, `main.tex`) and compiled `main.pdf`.
- `data/` — downloaded graphs (not tracked; see below).

## Environment
Python 3.11.2; numpy 2.4.6, scipy 1.17.1, networkx 3.6.1, pandas 3.1.0, matplotlib 3.11.2, scikit-learn 1.9.1 (full `pip freeze` in `requirements_freeze.txt`).
```
python3 -m venv venv && ./venv/bin/pip install numpy scipy networkx matplotlib scikit-learn pandas
```
LaTeX: `pdflatex` + `bibtex` (TeX Live), ICML 2026 style files (copied into `paper/`; downloaded from https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip).

## Data (public graphs, no account needed)
```
mkdir -p data/stanford3 data/egofb
curl -L -o data/stanford3/socfb-Stanford3.zip https://nrvis.com/download/data/socfb/socfb-Stanford3.zip   # sha256 b1221e41...5e8720d (verified)
unzip data/stanford3/socfb-Stanford3.zip -d data/stanford3
curl -L -o data/egofb/facebook_combined.txt.gz https://snap.stanford.edu/data/facebook_combined.txt.gz     # sha256 125e84db...ad035d7 (verified)
gunzip -k data/egofb/facebook_combined.txt.gz
```
Synthetic graphs are generated from seeds (population seed 0). Louvain partitions are cached in `results/cache/`.

## Seeds, runtime
Replicate `r` of configuration `c` uses `numpy.random.default_rng([2026, crc32(json(c)), r])`; population seed 0 (graph, baselines, community effects fixed per configuration; Louvain seed 0). The machine had 4 usable CPU cores (cgroup limit; `nproc` reports more); set `NPROC=<cores>`. Measured wall-clock on 4 cores: e1 36 s, e2 25 min, e3 22 min, e4 4.3 min, e5 13 min, e6 20 min, e7 9 s, e8 13 s, e9 7 min, e10 13 min, e11 23 s (≈1.9 h total). Memory < 2 GB.

## Commands
```
cd code
./run_all.sh          # e1..e9  (note: its e6 run crashed on the original 30-block SBM; see below)
./run_rest.sh         # e6 (fixed: 15 SBM blocks), e10, e11
./make_all.sh         # all figures / tables -> figs/, paper/tables/, results/summary_*.csv, results/out_*.txt
cd ../paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```
Process note: the first `e6_degree` run crashed (SBM edge probability > 1 at mean degree 128 with 100-node blocks); `experiments.py` now uses 15 blocks of 200 nodes for e6, and `run_rest.sh` re-runs it. `run_all.sh` as shipped still lists e6; its crashed output is overwritten by `run_rest.sh`.

## Which script produces which artifact
| Artifact in paper | Data | Script |
|---|---|---|
| Fig. 1 (noise term) | e1 | fig_e1.py |
| Table 1, Fig. 7-8 (main grid, appendix heatmaps) | e2 | tab_e2.py, fig_e2.py |
| Fig. 2 (bias vs p, theory) | e9 | fig_e9.py (+ analysis_common.slope_pred) |
| Fig. 3 (degree sweep) | e6 | fig_e6.py |
| Fig. 4, Table 2 (designs) | e3 | fig_e3.py |
| Fig. 5 (graph corruption) | e8 | fig_e8.py |
| Fig. 6, R2/R9 numbers (diagnostics) | e1-e6, e8-e10 | fig_diag.py |
| Table 3, Table 8 (coverage) | e7 | tab_e7.py |
| Fig. 9 (n-scaling) | e4 | fig_e4.py |
| Fig. 10 (gamma, sigma) | e5 | fig_e5.py |
| Table 5 (theory check) and R3 numbers | e6, e9 | stats_theory.py, tab_theory.py |
| Table 6 (cluster granularity), Table 7 (homophily) | e10, e11 | fig_e10.py, tab_app.py |
Figure/table numbers follow the compiled PDF; `paper/main.tex` captions and Appendix A (Table "Experiment -> script -> artifact") are authoritative.

## Notes on access restrictions
Only the starter-list papers and exact-title searches for well-known, unrelated papers were used (OpenAlex/arXiv API metadata). No excluded material was knowingly encountered.
