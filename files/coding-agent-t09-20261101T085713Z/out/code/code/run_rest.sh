#!/bin/sh
# experiments run after run_all.sh (e6 was re-run after fixing the SBM block size; e10/e11 added later)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NPROC=${NPROC:-4}
cd "$(dirname "$0")"
for e in e6_degree e10_clusterres e11_homophily; do
  ../venv/bin/python experiments.py $e > ../results/log_$e.txt 2>&1
done
