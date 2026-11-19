#!/bin/bash
# H3 (nonlinear imputers, mixture, adaptivity).  usage: exp/e_h3.sh FIRST LAST
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
for r in $(seq $1 $2); do
  for s in A2 A1; do
    [ -f results/H3/$s/h3_rep$r.parquet ] || python3 -I exp/e_h3.py $s results/H3/$s --rep $r --ks 1,3,8,12,20
  done
  [ -f results/H3/HELMMMLU/h3_rep$r.parquet ] || python3 -I exp/e_h3.py HELMMMLU results/H3/HELMMMLU --rep $r --ks 1,3,8,12,20
done
echo "HUTIAN_WAKE: h3 $1-$2 finished"
