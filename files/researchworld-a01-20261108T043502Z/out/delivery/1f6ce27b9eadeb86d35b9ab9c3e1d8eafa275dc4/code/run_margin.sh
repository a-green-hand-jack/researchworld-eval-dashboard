#!/bin/bash
# margin sensitivity: strict-first requires a lead of EPS score points (default runs use 0.001), EPS = 1 and 2
cd "$(dirname "$0")/.."
for e in 1 2; do
  python3 -u code/run_core.py helm emp99T mean,median,min,borda,condorcet,plurality all results/margin${e}_helm.csv --eps $e
  python3 -u code/run_core.py ollb emp99 mean,median,min all results/margin${e}_ollb.csv --eps $e
done
