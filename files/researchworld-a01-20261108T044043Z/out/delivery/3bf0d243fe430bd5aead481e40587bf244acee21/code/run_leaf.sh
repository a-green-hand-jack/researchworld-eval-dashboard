#!/bin/bash
# OLLB leaf-task run (39 leaf tasks: 24 BBH, 3 GPQA, 7 MATH-hard, 3 MuSR, MMLU-PRO, IFEval) against the six published tasks of the SAME
# 499 models.  Prerequisite (network, once): python3 code/fetch_ollb_leaves.py RAW 500 && python3 code/build_ollb_leaves.py RAW
#   data/processed/ollb_leaves.csv results/ollb_leaves_gate.json   (the shipped data/processed/ollb_leaves.csv is its output)
# Usage: bash code/run_leaf.sh STEP   with STEP in closed_leaf closed_six ord_leaf ord_six (independent, run in parallel), then `assemble`.
set -euo pipefail
R=results/leaf; mkdir -p $R
case $1 in
 closed_leaf) python3 code/run_core.py ollb_leaf ceil,gain10,emp99task mean,median,min all $R/runs_closed_leaf.csv ;;
 closed_six)  python3 code/run_core.py ollb6_leafslice ceil,gain10,emp99 mean,median,min all $R/runs_closed_six.csv ;;
 ord_leaf)    python3 code/run_core.py ollb_leaf ceil,gain10,emp99task borda,condorcet,plurality top50 $R/runs_ord_leaf.csv ;;
 ord_six)     python3 code/run_core.py ollb6_leafslice ceil,gain10,emp99 borda,condorcet,plurality top50 $R/runs_ord_six.csv ;;
 *) echo unknown step; exit 1 ;;
esac
