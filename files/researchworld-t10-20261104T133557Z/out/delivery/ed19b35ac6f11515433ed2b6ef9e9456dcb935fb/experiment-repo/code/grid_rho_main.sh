#!/bin/bash
# labeled-to-unlabeled ratio sweep on census_income: n=200, N in {200,2000,20000}; 2000 reps.
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
OUT=${OUT:-/hutian/scratch/raw/rho_real}; mkdir -p $OUT; cd "$(dirname "$0")"
for N in 200 2000 20000; do f=$OUT/census_income_n200_N${N}.csv; [ -f $f ] || BOOT=1 python3 run_real.py census_income 200 2000 7 $f $N 2; done
echo "HUTIAN_WAKE: rho sweep finished"
