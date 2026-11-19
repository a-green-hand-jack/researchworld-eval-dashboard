#!/bin/sh
# Rebuild every figure and table of the delivery from results/.  usage: sh figures/scripts/build_all.sh   (from the repository root)
set -e
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
cd "$here"
for s in make_fig1 make_fig2 make_fig3 make_fig4 make_fig5; do python3 $s.py --results "$root/results" --out "$root/figures"; done
python3 make_tables.py --results "$root/results" --out "$root/tables"
