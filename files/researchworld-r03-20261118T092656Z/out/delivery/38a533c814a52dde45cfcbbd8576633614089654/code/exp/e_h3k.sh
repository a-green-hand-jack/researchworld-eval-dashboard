#!/bin/bash
# H3 large-k addendum: selector (greedyAcomp) vs random under FA / ExtraTrees / kernel ridge at k = 20, 30 (A2: 20 only, N = 30).  usage: exp/e_h3k.sh FIRST LAST
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
for r in $(seq $1 $2); do
  [ -f results/H3k/A2/h3_rep$r.parquet ] || python3 -I exp/e_h3.py A2 results/H3k/A2 --rep $r --ks 20 --n_random 20
  for s in A1 HELMMMLU; do
    [ -f results/H3k/$s/h3_rep$r.parquet ] || python3 -I exp/e_h3.py $s results/H3k/$s --rep $r --ks 20,30 --n_random 20
  done
done
echo "HUTIAN_WAKE: h3k $1-$2 finished"
