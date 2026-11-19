#!/usr/bin/env bash
# Main sweep: all benchmarks x {random, extrap} protocols x 20 reps x 10 methods x 5 budgets.  usage: run_main.sh "bench1 bench2 ..."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
set -e; cd "$(dirname "$0")/.."
for b in $1; do for p in random extrap; do
  python3 -I src/run.py --bench $b --protocol $p --reps 20 --out results/raw/main
done; done
