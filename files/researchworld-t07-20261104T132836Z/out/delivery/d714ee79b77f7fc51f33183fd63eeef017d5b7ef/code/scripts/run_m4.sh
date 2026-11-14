#!/usr/bin/env bash
# Proposed method (mass_ens, with interval widths), sources-only reference (null), ridge-AIPW variants and MASS ablations on the main grid.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
set -e; cd "$(dirname "$0")/.."
for b in $1; do for p in random extrap; do
  python3 -I src/run.py --bench $b --protocol $p --reps 20 --methods mass_ens,sources_only,aipw_ridge_repo,aipw_ridge_cf,mass_sel,mass_ens_nocorr,ens_rand_nocorr --out results/raw/m4
done; done
