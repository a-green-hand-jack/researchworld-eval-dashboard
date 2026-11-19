#!/bin/bash
# OLS coefficients on census_income (Y ~ age + sex, no intercept), N=10000, 2000 reps.
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
OUT=${OUT:-/hutian/scratch/raw/ols_real}; mkdir -p $OUT; cd "$(dirname "$0")"
for n in 50 100 200 500 1000; do f=$OUT/census_income_n${n}.csv; [ -f $f ] || python3 run_ols.py census_income $n 2000 3 $f 10000 2; done
echo "HUTIAN_WAKE: ols grid finished"
