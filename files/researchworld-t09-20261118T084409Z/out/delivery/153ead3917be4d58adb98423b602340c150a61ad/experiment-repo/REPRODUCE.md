# Reproduction

Everything is CPU-only Python; no GPU, no network after the two graph files are downloaded. All commands are run from the root of
this tree (the directory that contains `code/`, `results/` and this file).

## Environment
    python 3.11.2
    numpy 2.4.6   scipy 1.17.1   pandas 3.0.6   pyarrow 26.0.0   networkx 3.6.1   scikit-learn 1.9.1   torch 2.14.1 (CPU)
    pip install numpy scipy pandas networkx scikit-learn pyarrow torch --index-url https://download.pytorch.org/whl/cpu   # torch only for the GCN estimator (grid e6)
Dependencies are listed in `code/requirements.txt`. `results/provenance.json` records the versions, a hash of the code and the seeds used for each file.

## Data (two public graphs, no account needed; everything else is simulated)
    mkdir -p data/raw && cd data/raw
    curl -fLO https://nrvis.com/download/data/socfb/socfb-Stanford3.zip
    curl -fLO https://snap.stanford.edu/data/facebook_combined.txt.gz
    sha256sum -c <<'H'
    b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d  socfb-Stanford3.zip
    125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7  facebook_combined.txt.gz
    H
The loader reads `data/raw` (override with `NETGATE_DATA`). Stanford3: 11,586 nodes, 568,309 edges (Traud, Mucha and Porter 2012; Network Repository, CC BY-SA).
ego-Facebook: 4,039 nodes, 88,234 edges (McAuley and Leskovec 2012; SNAP, citation requested). The graphs are not redistributed in this tree.
Both are reduced to their largest connected component; the parameter `q` < 1 keeps each edge with probability q under a fixed seed to vary the degree on real topology.
Outcomes are synthetic on every graph (the real graphs supply topology only).

## Layout
* `code/netgate/` — the bench: `graphs.py`, `outcomes.py` (fixed potential outcomes, exact GATE), `ctx.py` (exposure map), `designs.py` (Bernoulli, graph cluster randomisation),
  `estimators.py` (DM, REG-L / -Lc / -Q / -G / -O, HT and Hájek with relaxed exposure, exact HT variance), `theory.py` (exact projection bias, leverage),
  `intervals.py` (iid / HC2 / HC3 / network sandwich / cluster-robust / assignment-resampling standard errors), `diagnostics.py`, `ml.py` (boosting, GCN), `runner.py`, `grids.py`.
* `code/scripts/` — `run_grid.py <grid>`, `summarize.py <grid>`, `analyze_c3.py`, `analyze_c4.py`, `analyze_c5.py`, `analyze_c6.py`, `analyze_c11.py`, `analyze_c12.py`, `analyze_c13.py`, `fig1_corner.py`, `provenance.py`; `code/PREREG.md` — the diagnostic and interval, fixed before grid e7 was generated (its D4 addendum before e12).
* `results/raw/<grid>.parquet` (one row per replicate), `results/summary/<grid>.csv` (one row per cell × estimator, Monte-Carlo CIs), `results/fig1_corner.parquet`,
  `results/provenance.json`, `results/README.md` (column schema), `results/STATUS.md` (what ran), `results/SUMMARY.md` (findings with the conditions they hold under).

## Seeds
Every cell is seeded from the SHA-256 of its configuration xor `--seed` (default 0); replicate r uses the r-th child of that `SeedSequence`. Grids that extend another
(`e3c` on `e3`) replay its draws through the `seed_cfg` field, so estimators are compared on identical replicates. `e10` fixes the graph, the heterogeneity and the noise per cell and
redraws only the assignment (the pure design variance).

## Commands (one grid = one command; cells are cached in `$NETGATE_WORK`, default `work/`, so an interrupted run resumes)
    python code/scripts/run_grid.py <grid> --workers 2        # writes results/raw/<grid>.parquet
    python code/scripts/summarize.py <grid>                    # writes results/summary/<grid>.csv
    python code/scripts/run_grid.py <grid> --reverse --workers 2  # optional second runner on the same cache, from the last cell (e6 only); the first runner writes the table
    python code/scripts/analyze_c3.py                          # needs e3 and e3c
    python code/scripts/analyze_c4.py                          # needs e4
    python code/scripts/analyze_c5.py                          # needs e6 (and its summary)
    python code/scripts/analyze_c6.py                          # needs e7 (PREREG.md)
    python code/scripts/analyze_c11.py                         # needs e11 (and its summary)
    python code/scripts/analyze_c12.py                         # needs e12 (D4; PREREG.md addendum)
    python code/scripts/analyze_c13.py                         # needs the graphs and e6 (exact projection bias, plateau mass; no new grid)
    python code/scripts/fig1_corner.py
    python code/scripts/provenance.py

| grid | what | cells × replicates | claim |
|---|---|---|---|
| e1 | iid slice: n × d × p × σ, correct model | 150 × 400 | C1 |
| e1b | C1 across graph families | 32 × 300 | C1 |
| e2 | bias vs exact projection: κ × shape × p × d × σ | see `results/provenance.json` | C2 |
| e2b | bias plateau in n | 24 × 200 | C2 |
| e3, e3c | regression vs HT / relaxed Hájek / DM as d grows (e3c adds δ on the same draws) | 100 × 300 | C3 |
| e4 | collapse in Z across graph families, incl. thinned Stanford3 and ego-Facebook | see provenance | C4 |
| e5 | GCR cluster scale | see provenance | C7 |
| e6 | method × mechanism × graph map (incl. boosting, GCN) | 60 × 100 | C5 |
| e7 | pre-registered diagnostic and interval | 480 × 120 | C6 |
| e12 | D4 degree transport (BA / Stanford3 / ego-Facebook vs ER control; responses without and with degree dependence) | 132 × 100 | C6 (D4) |
| e11 | observed-graph error q × interference range (1 vs 2 hops) | 80 × 100 | C5 (H4) |
| e8 | staggered rollout at matched measurements | 24 × 150 | C7 |
| e9 | standard-error / interval comparison as n grows | see provenance | C1, C6 |
| e10 | design-only variance (graph, heterogeneity, noise frozen; assignment redrawn) with the same standard errors | 128 × 500 | C1, C6 |

## Compute (measured on shared 2-CPU containers; CPU-seconds = wall × 2)
| grid | wall (s) | CPU-s | note |
|---|---|---|---|
| e1b | 384 | 768 | |
| e2b | 64 | 128 | |
| e3 | 1088 | 2176 | exact HT variance included |
| e1 | 2720 | 5440 | 150 cells × 400 replicates; shared host (wall time depends on load) |
| e2 | 4104 | 8208 | 320 cells × 200 replicates |
| e10 | 5359 | 10718 | 128 cells × 500 replicates, 8 standard errors per replicate |
| e8 | 20 | 40 | |
| e3c | < 60 | < 120 | no exact HT variance |
| e5 | 8016 | 16032 | 112 cells × 150 replicates, Louvain partitions per replicate |
| e4 | 14933 | 29866 | 261 cells × 200 replicates, incl. Stanford3 up to n = 11586 |
| e9 | 17285 | 34570 | 48 cells × 100 replicates, 9 intervals each (resampling B=100), shared host |
| e7 | 30523 | 61046 | 480 cells × 120 replicates; 2 bootstrap intervals (B=200) and 3 diagnostics per replicate |
| e6 | 98114 | 196228 | 60 cells × 100 replicates; GCN (200 epochs) and boosting per replicate, Stanford3 cells dominate; the last cells were also run by a second runner on the same cache (`--reverse`), so wall time is shorter than the CPU time of the cells |
| e12 | 641 | 1282 | 132 cells × 100 replicates; D1–D4 and 4 regressions per replicate, no bootstrap intervals |
| e11 | 339 | 678 | 80 cells × 100 replicates, 4 regressions and an exact projection bias per replicate |

Total for the whole study, summing the CPU-s column (e3c at its bound), is about 3.7 × 10^5 CPU-s, roughly 100 CPU-hours; the heaviest grids are e6 (53% of it; GCN and boosting on real graphs), e7 (17%), e9 (9%) and e4 (8%). The other eleven grids together take about 13 CPU-hours.

## Figure/table → script
Figures and tables are produced by the scripts of `figures/src/` and `tables/src/` listed in `figures/FIGURES.md` (run from the repository root, `python3 -I <script>`), which read only `results/`. Labels are the paper's; figtab's internal names are in parentheses. Files are under `results/` (`summary/` unless a path is given); the analysis scripts named run `PYTHONPATH=code python code/scripts/<script>` on the raw grids.

| Paper item | Result files | Analysis script |
|---|---|---|
| Fig. 1 (corner) | `fig1_corner.parquet` | `fig1_corner.py` |
| Fig. 2 (anatomy; C1) | `e1.csv`, `e1b.csv`, `e9.csv` (and `e10.csv` for the text) | `summarize.py` |
| Fig. 3 (projection bias; C2) | `e2.csv`, `e2b.csv` | `summarize.py` |
| Fig. 4 (crossover; C3) | `e3.csv`, `e3c.csv`, `c3_pairs.csv` | `analyze_c3.py` |
| Fig. 5 (collapse; C4) | `e4.csv`, `c4_variance.csv`, `c4_bias_loo.csv`, `c4_bias_pred.csv` | `analyze_c4.py` |
| Table 1 (mechanism × method; C5) | `c5_table1.csv` (median/worst over graphs, with CIs), `c5_cells.csv` (full grid), `c5_best.csv` (best non-oracle method per cell) | `analyze_c5.py` |
| Fig. 6 (diagnostics; C6) (a) 480 cells; (c) bound B | `raw/e7.parquet`, `e7.csv`, `c6_rank.csv`, `c6_flag.csv`, `c6_auc_by_mech.csv`, `c6_B_vs_bias.csv` | `analyze_c6.py` |
| Fig. 6(b) (D4 on grid e12) | `c12_cells.csv`, `c12_rank.csv`, `c12_flag.csv`, `c12_estimator.csv`, `c12_by_graph.csv` | `analyze_c12.py` |
| Table 2 (paired comparison, appendix; C3/C5) | `c3_pairs.csv` | `analyze_c3.py` |
| Fig. 7 (misspecified graph; H4) (appendix) | `e11.csv`, `c11_map.csv`, `c11_check.csv` | `analyze_c11.py` |
| Fig. 8 (cluster scale; C7) (appendix) | `e5.csv` | `summarize.py` |
| Table 3 (staggered rollout; C7) (appendix) | `e8.csv` | `summarize.py` |
| Fig. 9 (D1 against bias) (appendix) | `c6_cover_cells.csv` | `analyze_c6.py` |
| Tables 4 and 5 (median, worst over graphs, with intervals) | `c5_table1.csv` | `analyze_c5.py` |
| Tables 6 and 7 (coverage and width, by class and by regime) | `c6_cover.csv`, `c6_cover_cells.csv` | `analyze_c6.py` |
| Real-graph threshold mechanism (text of Section 5, F13 in `results/SUMMARY.md`) | `c13_exposure.csv`, `c13_fit_subset.csv` | `analyze_c13.py` |
