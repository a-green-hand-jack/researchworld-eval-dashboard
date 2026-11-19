#!/bin/bash
# H3 addendum: random-selection counterpart for FA / ExtraTrees / kernel ridge (same folds/seeds as e_h3.sh; 20 draws).  usage: exp/e_h3r.sh FIRST LAST
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
for r in $(seq $1 $2); do
  for s in A2 A1 HELMMMLU; do
    [ -f results/H3r/$s/h3_rep$r.parquet ] || python3 -I exp/e_h3.py $s results/H3r/$s --rep $r --ks 3,8,12 --n_random 20
  done
done
echo "HUTIAN_WAKE: h3r $1-$2 finished"
