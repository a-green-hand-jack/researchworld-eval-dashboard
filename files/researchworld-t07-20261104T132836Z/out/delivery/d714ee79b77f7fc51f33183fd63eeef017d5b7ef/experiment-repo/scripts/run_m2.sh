#!/usr/bin/env bash
# Second sweep: model-assisted designs / ablations (methods2.py). usage: run_m2.sh "bench1 bench2 ..."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
set -e; cd "$(dirname "$0")/.."
for b in $1; do for p in random extrap; do
  python3 -I src/run.py --bench $b --protocol $p --reps 20 --methods mass,aipw_strat,aipw_pps,ppi,aipw_knn,aipw_ens,aipw_k1,aipw_k4,mass_k1,mass_k4 --out results/raw/m2
done; done
