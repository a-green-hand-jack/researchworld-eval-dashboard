#!/usr/bin/env bash
# Full pipeline (about 30 min on 4 CPU cores).  Assumes data/ is populated (./get_data.sh)
# and the Python environment in requirements.txt is active.  NPROC sets worker processes (default 4).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p derived results figs paper/tables
python code/data_prep.py                # derived/*.parquet, derived/meta.json            (~10 s)
python code/run_pairs.py                # results/pairs.parquet                            (~5 min)
python code/pair_influence.py           # results/pair_influence.parquet                   (<1 min)
python code/bootstrap_k.py 100          # results/bootstrap_k.parquet                      (~10 min)
python code/random_noise.py 200         # results/random_noise.parquet                     (~2 min)
python code/realistic_attack.py 20      # results/realistic_attack.parquet                 (~2 min)
python code/relaxation_check.py         # results/relaxation_check.parquet                 (~2 min)
python code/subsample.py 10             # results/subsample.parquet                        (~1 min)
python code/matched_mt6.py 100          # results/matched_mt6.parquet                      (~1 min)
python code/composition.py              # results/composition.json                         (<1 min)
python code/analysis_law.py             # figs/fig_law.pdf, paper/tables/law.tex           (~3 min)
python code/analysis_tables.py          # remaining tables/figures, results/numbers.json   (~1 min)
cd paper && latexmk -pdf -interaction=nonstopmode main.tex
