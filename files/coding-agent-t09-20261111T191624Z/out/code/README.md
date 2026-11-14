# Regression-based GATE estimation under network interference — code, results and paper

Everything needed to reproduce the paper in `paper/main.pdf` (NeurIPS 2026 template, `paper/main.tex`).
All outcomes are synthetic; the only external data are two public graphs.

## Layout
```
code/        simulation library (sim.py, graphs.py, theory.py), experiments (experiments.py, run_all.sh),
             exact multi-hop statistics (psi.py), figure/table/number scripts (fig_*.py, mk_tables.py, stats_summary.py, verify_claims.py)
data/        raw downloads (stanford3_raw/, ego_raw/)      [created by run_all_experiments.sh]
results/     E1..E7.csv, E2g.csv, psi.json, logs, cluster_cache/ (Louvain labels of the real graphs), pilot/ (3-world pilot, superseded)
paper/       main.tex, sec_*.tex, refs.bib, neurips_2026.sty, figs/, tables/, main.pdf
requirements.txt, run_all_experiments.sh
```

## Environment
Python 3.11.2 (venv), numpy 2.4.6, scipy 1.17.1, networkx 3.6.1, pandas 3.1.1, scikit-learn 1.9.1, matplotlib 3.11.2 (see `requirements.txt`;
`pypdf`/`pymupdf` only for page-count helpers, not needed for results). pdfLaTeX + bibtex for the paper.
Hardware used: CPU only, container limited to 4 cores (cgroup quota), 251 GB RAM available.

## Data (versions)
| graph | source | file | sha256 (verified) |
|---|---|---|---|
| Facebook100 / Stanford3 (n=11,586, m=568,309) | https://nrvis.com/download/data/socfb/socfb-Stanford3.zip (Network Repository, CC BY-SA; Traud, Mucha & Porter 2012; Rossi & Ahmed 2015) | `socfb-Stanford3.mtx` in the zip (1,649,740 bytes) | b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d |
| SNAP ego-Facebook (n=4,039, m=88,234) | https://snap.stanford.edu/data/facebook_combined.txt.gz (McAuley & Leskovec 2012) | `facebook_combined.txt.gz` (218,576 bytes) | 125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7 |

Downloaded files are untrusted: they sit in their own directories under `data/` and are parsed as plain text by `code/graphs.py` (never executed).
Synthetic graphs (ER, random regular, SBM, Watts–Strogatz, Barabási–Albert) are generated with networkx.

## Reproduce (≈1 h wall-clock on 4 cores; ≈4 CPU-hours)
```
./run_all_experiments.sh          # venv, data, E1..E7 (+E2g), psi.py, all figures/tables/numbers, paper
```
or step by step from `code/`:
```
./run_all.sh E1 E2 E2g E3 E4 E5 E6 E7         # writes ../results/E*.csv   (times below)
../venv/bin/python psi.py                      # results/psi.json (exact walk statistics used by Prop. 5 / Fig. 3)
../venv/bin/python fig_variance.py             # Fig. 1  (+ tables/pred_ratio_by_family.csv)
../venv/bin/python stats_summary.py            # headline numbers -> paper/tables/headline_numbers.json (needed by fig_extrap.py, mk_tables.py)
../venv/bin/python fig_extrap.py               # Fig. 2
../venv/bin/python fig_multihop.py             # Fig. 3  (+ tables/multihop*.csv)
../venv/bin/python fig_crossover.py            # Fig. 4  (+ tables/crossover.csv)
../venv/bin/python fig_design.py               # Fig. 5
../venv/bin/python fig_inference.py            # Fig. 6 (appendix)
../venv/bin/python fig_obsnoise.py             # Fig. 7 (appendix)
../venv/bin/python stats_summary.py; ../venv/bin/python mk_tables.py; ../venv/bin/python verify_claims.py
cd ../paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```
Wall-clock of the final runs (4 processes): E1 172 s, E2 473 s, E2g 181 s, E3 355 s, E4 177 s, E5 1269 s, E6 858 s, E7 64 s, psi.py ≈ 4 min.
(`experiments.run(procs=4)` — change `procs` for other machines.)

## Experiments
| id | question | file |
|---|---|---|
| E1 | variance vs degree, n, noise, graph family, design (linear response) | results/E1.csv |
| E2 | nonlinear exposure response, flexible regressions, Hájek (E2g: gradient boosting, 3 worlds × 40 assignments) | E2.csv, E2g.csv |
| E3 | multi-hop spillover, degree-heterogeneous spillover, count vs fraction exposure | E3.csv |
| E4 | regression vs difference-in-means as spillover strength varies | E4.csv |
| E5 | treated fraction p and number of clusters | E5.csv |
| E6 | coverage of HC / community-clustered / 2-hop HAC intervals | E6.csv |
| E7 | mis-measured graph | E7.csv |

Each CSV row = one (world, setting, estimator): bias, SD, RMSE over R assignments, failure rate (H\'ajek undefined), mean leverage, closed-form
leverage (`lev_theory`), closed-form Bernoulli bias (`proj_bias_theory`), coverage columns (E6), cluster statistics.

## Seeds
World i = 0..5: synthetic graph seed 100+i, outcome-parameter seed 1000+i (real graphs: graph fixed, parameter seed 1000+i).
Assignment RNG of a configuration: first 8 hex digits of SHA-256 of its (graph, mechanism, design, i) JSON (`experiments.stable_seed`).
Louvain seed 1 (labels for the real graphs are cached in `results/cluster_cache`). Verified: re-running E7 gives bit-identical numeric output.

## Figure / table → script
Fig. 1 `fig_variance.py` (E1) · Fig. 2 `fig_extrap.py` (E2) · Fig. 3 `fig_multihop.py` (E3, psi.json) · Fig. 4 `fig_crossover.py` (E4) · Fig. 5 `fig_design.py` (E5) ·
Fig. 6 (appendix) `fig_inference.py` (E6) · Fig. 7 (appendix) `fig_obsnoise.py` (E7) · Table 1 `mk_tables.py:tab_het` (E3) · appendix tables `mk_tables.py` (tab_extrap, tab_mh, tab_lev, tab_siga, tab_clu, tab_cross) ·
quoted numbers: `stats_summary.py`, `verify_claims.py` (prints every number used in Section 6 text), exact-formula table `fig_multihop.py`.

## Honest notes
* A 3-world pilot of E1/E3 (results/pilot/) set the run scale; it exposed a crash (cluster assignments with an empty arm for ≤10 clusters) — fixed by redrawing such assignments; final results use 6 worlds.
* An early attempt to run on 36 processes was slowed by the 4-core CPU quota; E2 originally contained gradient boosting for 200 assignments and was split into E2/E2g (40 assignments) for cost.
* `wls_s` and `strat_s` estimators were added after seeing the pilot heterogeneity results (E3 was re-run with them; other E3 outputs are identical because seeds are config-derived).
* Closed forms are population/first-order statements; the cluster-design leverage formula underpredicts RMSE in 73% of runs (see paper).
* Literature access: only the starter literature and unrelated public papers were consulted. No page matching the withheld paper was knowingly opened. Title/abstract snippets of a few unrelated
  network-interference papers appeared incidentally in search results (e.g. on surrogate networks, two-stage rollouts, mixed randomization) and were not read further.
* Paper template: official NeurIPS 2026 files (`neurips_2026.sty`, checklist) from https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip (the style file is used unmodified; the main text is 9 pages, references/appendix/checklist follow).
* `results/verify_claims_output.txt` and `results/stats_summary_output.txt` hold the printed numbers used to check every quantitative statement in Section 6 and the abstract.
