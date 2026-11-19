#!/bin/bash
# usage: exp/loop.sh SETTING FIRST_REP LAST_REP [extra args]
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
s=$1; a=$2; b=$3; shift 3
for r in $(seq $a $b); do
  [ -f results/$s/rec_rep$r.parquet ] || python3 -I exp/run_cv.py --setting $s --rep $r --out results/$s "$@"
done
echo "HUTIAN_WAKE: loop $s $a-$b finished"
