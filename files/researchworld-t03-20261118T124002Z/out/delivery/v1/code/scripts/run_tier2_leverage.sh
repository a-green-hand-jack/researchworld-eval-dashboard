#!/bin/bash
# Tier 2: Leverage SHAP arm (R=20, same budget grid) on every cell that has an R=20 grid. usage: run_tier2_leverage.sh CELL...
cd "$(dirname "$0")/.."
export PYTHONPATH=.
for c in "$@"; do
  python3 -u scripts/run_estimators.py --cell $c --R 20 --tag T2 --arms leverage --mults 0.25,0.5,1,2,4,16 && python3 scripts/summarize_cell.py --cell $c --tag T2 | tail -1
done
