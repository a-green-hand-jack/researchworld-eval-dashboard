#!/bin/bash
# H3 full-grid addendum: greedyAcomp and random under FA / ExtraTrees / kernel ridge on the whole k grid of the curves (lean: no mixture, no wrapper).  usage: exp/e_h3c.sh SETTING FIRST LAST
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
case $1 in A1) KS=1,2,3,4,5,6,8,10,12,15,20,30;; A2) KS=1,2,3,4,5,6,8,10,12,15,20;; esac
for r in $(seq $2 $3); do
  [ -f results/H3c/$1/h3_rep$r.parquet ] || python3 -I exp/e_h3.py $1 results/H3c/$1 --rep $r --ks $KS --n_random 20 --lean
done
echo "HUTIAN_WAKE: h3c $1 $2-$3 finished"
