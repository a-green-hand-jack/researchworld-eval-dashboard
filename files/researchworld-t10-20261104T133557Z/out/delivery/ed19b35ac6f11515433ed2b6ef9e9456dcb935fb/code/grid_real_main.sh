#!/bin/bash
# usage: grid_real_main.sh DATASET [NS] [REPS]   Mean CIs (+ Wald/t/studentised) on one real pool; raw rows -> $OUT.
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
OUT=${OUT:-/hutian/scratch/raw/mean_real}; mkdir -p $OUT
d=$1; NS=${2:-"50 100 200 500 1000"}; REPS=${3:-2000}
cd "$(dirname "$0")"
for n in $NS; do
  f=$OUT/${d}_n${n}.csv
  [ -f $f ] || BOOT=1 python3 run_real.py $d $n $REPS 1 $f 10000 2
done
echo "HUTIAN_WAKE: mean grid $d finished"
