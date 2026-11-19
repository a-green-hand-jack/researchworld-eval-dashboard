#!/bin/bash
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
for r in 0 1 2 3 4; do
  for s in A2 HELMMMLU HELMLITE A1; do [ -f results/E6/$s/e6_${s}_rep$r.parquet ] || python3 -I exp/e6_shift.py $s results/E6/$s --rep $r; done
  [ -f results/E6/OLMB40/e6_OLMB40_rep$r.parquet ] || python3 -I exp/e6_shift.py OLMB40 results/E6/OLMB40 --rep $r --max_models 1500 --kgrid 1,2,3,5,8,12,20,30
  [ -f results/E6/OLMB6/e6_OLMB6_rep$r.parquet ] || python3 -I exp/e6_shift.py OLMB6 results/E6/OLMB6 --rep $r --max_models 1500 --kgrid 1,2,3,4,5
done
echo "HUTIAN_WAKE: e6 finished"
