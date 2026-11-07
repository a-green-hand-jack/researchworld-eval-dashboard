#!/bin/sh
# Regenerates every figure/table of the paper from results/*.csv.gz (run after run_all.sh, run_rest.sh and
# `python experiments.py e10_clusterres` / e11_homophily, which run_rest.sh includes).
cd "$(dirname "$0")"
PY=../venv/bin/python
for s in fig_e1 fig_e2 tab_e2 fig_e3 fig_e4 fig_e5 fig_e6 tab_e7 fig_e8 fig_e9 fig_e10 stats_theory tab_theory fig_diag tab_app build_tabular; do
  echo "== $s"; $PY $s.py > ../results/out_$s.txt 2>&1 || echo "FAILED $s"
done
