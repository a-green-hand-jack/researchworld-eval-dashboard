#!/bin/sh
# Rebuild every delivered figure and table.  Usage: sh run_all.sh <results-dir> <out-dir>
#   <results-dir>: experiment-repo's results/ (paper-repo main: results/); the scripts address it as data_in/.
#   <out-dir>: receives figures/*.{pdf,png} and tables/*.tex.  Needs python3 with numpy, pandas, matplotlib (3.11.2 used).
set -e
SRC=$(cd "$(dirname "$0")" && pwd); RES=$(cd "$1" && pwd); mkdir -p "$2"; cd "$2"; mkdir -p figures tables
ln -sfn "$RES" data_in
for s in fig_headroom_population fig_validity fig_c2_real fig_c3_synth tab_datasets tab_headroom tab_ols; do python3 "$SRC/$s.py"; done
