#!/bin/sh
# Runs every experiment sequentially (about 3-5 h on 4 CPU cores).
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NPROC=${NPROC:-4}
cd "$(dirname "$0")"
for e in e1_var e2_main e3_design e4_scale e5_dosenoise e6_degree e7_infer e8_misspec_graph e9_prob e10_clusterres; do
  ../venv/bin/python experiments.py $e > ../results/log_$e.txt 2>&1
done
