#!/usr/bin/env bash
# Proposed method (mass_ens) on the main grid.  usage: run_m3.sh "bench ..."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
set -e; cd "$(dirname "$0")/.."
for b in $1; do for p in random extrap; do
  python3 -I src/run.py --bench $b --protocol $p --reps 20 --methods mass_ens,mass_ens_k2 --out results/raw/m3
done; done
