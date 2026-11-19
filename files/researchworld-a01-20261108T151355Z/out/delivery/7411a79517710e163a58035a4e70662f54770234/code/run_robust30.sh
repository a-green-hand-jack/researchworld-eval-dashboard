#!/bin/bash
# Extension of the C7 pilots to ~30-40 rank-stratified targets (ranks 2-11 + log-uniform in rank). To be merged into run_all.sh (kept separate while other jobs were reading run_all.sh).
set -e; cd "$(dirname "$0")"
case "$1" in
  helm_noise30)    python3 -u src/run_robust.py noise helm mean,geomean,median,min,borda,condorcet,plurality gain10 results/helm_noise_gain10_t30.csv --R 100 --ntargets 40 --stratified ;;
  ollb_noise30)    python3 -u src/run_robust.py noise ollb mean,geomean,median,min gain10 results/ollb_noise_gain10_t30.csv --R 100 --ntargets 30 --stratified ;;
  helm_taskboot30) python3 -u src/run_robust.py taskboot helm mean,geomean,median,min,borda,condorcet,plurality gain10 results/helm_taskboot_gain10_t30.csv --R 100 --ntargets 40 --stratified ;;
  ollb_hstar_cond) python3 -u src/run_hstar.py ollb condorcet sample results/ollb_hstar_ord_condorcet.csv --nsample 100 ;;
  ollb_hstar_plur) python3 -u src/run_hstar.py ollb plurality sample results/ollb_hstar_ord_plurality.csv --nsample 100 ;;
  *) echo "unknown job $1" >&2; exit 99 ;;
esac
