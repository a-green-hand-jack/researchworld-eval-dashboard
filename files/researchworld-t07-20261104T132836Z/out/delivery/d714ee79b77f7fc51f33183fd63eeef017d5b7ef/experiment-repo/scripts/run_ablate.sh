#!/usr/bin/env bash
# Sensitivity grids (10 reps) on a reduced method set.  usage: run_ablate.sh "bench ..." [family]
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
set -e; cd "$(dirname "$0")/.."
M=sources_only,random,anchor,ridge,calib,irt_rand,aipw_rand,anchor_irt,aipw_ens,mass,mass_ens,mass_sel,aipw_ridge_cf
O=results/raw/ablate
for b in $1; do
  for f in 0.1 0.3; do python3 -I src/run.py --bench $b --protocol extrap --frac $f --label extrap_f${f/./} --reps 10 --methods $M --out $O; done
  for s in 0.25 0.5; do for p in random extrap; do python3 -I src/run.py --bench $b --protocol $p --src_frac $s --label ${p}_s${s/./} --reps 10 --methods $M --out $O; done; done
  for p in random extrap; do python3 -I src/run.py --bench $b --protocol $p --no_dedup --label ${p}_nodedup --reps 10 --methods $M --out $O; done
  if [ -n "$2" ]; then python3 -I src/run.py --bench $b --protocol family --reps 10 --methods $M --out $O; fi
done
