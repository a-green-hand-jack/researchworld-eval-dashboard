#!/bin/bash
# usage: grid_synth.sh "SCENARIOS" "NS" "RHOS" REPS    synthetic mean-CI grid; raw rows -> $OUT.
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
OUT=${OUT:-/hutian/scratch/raw/synth}; mkdir -p $OUT; cd "$(dirname "$0")"
for sc in $1; do for rho in $3; do for n in $2; do
  f=$OUT/${sc}_n${n}_rho${rho}.csv; [ -f $f ] || python3 run_synth.py $sc $n $rho $4 2 $f 2
done; done; done
echo "HUTIAN_WAKE: synthetic grid finished: $1"
