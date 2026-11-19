#!/bin/sh
# Full pipeline (data -> experiments -> figures/tables -> paper). Expected wall time on 4 CPU cores: ~1.2 h (see README).
set -e
cd "$(dirname "$0")"
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
# --- data (untrusted downloads go into their own directories; parsed as plain text by code/graphs.py)
mkdir -p data/stanford3_raw data/ego_raw
[ -f data/stanford3_raw/socfb-Stanford3.mtx ] || { curl -sL -o data/stanford3_raw/socfb-Stanford3.zip https://nrvis.com/download/data/socfb/socfb-Stanford3.zip; (cd data/stanford3_raw && unzip -o socfb-Stanford3.zip); }
[ -f data/ego_raw/facebook_combined.txt.gz ] || curl -sL -o data/ego_raw/facebook_combined.txt.gz https://snap.stanford.edu/data/facebook_combined.txt.gz
sha256sum data/stanford3_raw/socfb-Stanford3.zip data/ego_raw/facebook_combined.txt.gz   # expect b1221e41... and 125e84db...
cd code
./run_all.sh E1 E2 E2g E3 E4 E5 E6 E7          # experiments -> results/E*.csv
../venv/bin/python psi.py                       # exact walk statistics for Prop. 5 -> results/psi.json
../venv/bin/python fig_variance.py              # Fig. 1, tables/pred_ratio_by_family.csv
../venv/bin/python stats_summary.py             # headline numbers -> paper/tables/headline_numbers.json
../venv/bin/python fig_extrap.py                # Fig. 2, tables/extrap_table.csv
../venv/bin/python fig_multihop.py              # Fig. 3, tables/multihop*.csv
../venv/bin/python fig_crossover.py             # Fig. 4, tables/crossover.csv
../venv/bin/python fig_design.py                # Fig. 5
../venv/bin/python fig_inference.py             # Fig. 6, tables/inference.csv
../venv/bin/python fig_obsnoise.py              # Fig. 7, tables/obsnoise.csv
../venv/bin/python stats_summary.py             # (again: now includes E4 crossover numbers)
../venv/bin/python mk_tables.py                 # LaTeX tables
../venv/bin/python verify_claims.py             # recomputes every number quoted in the text (see README)
cd ../paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
