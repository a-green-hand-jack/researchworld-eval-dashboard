#!/bin/bash
# plankton (no-shift / shift) and ballots (subsample / width-only) protocols. Raw rows -> $OUT.
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
OUT=${OUT:-/hutian/scratch/raw/special}; REPS=${REPS:-1000}; mkdir -p $OUT
cd "$(dirname "$0")"
for c in plankton_noshift plankton_shift ballots_sub ballots_width; do
  for n in 25 50 100 200 400 1000; do
    if [[ $c == ballots_sub && $n -gt 400 ]]; then continue; fi
    if [[ $c == ballots_width && $n -gt 400 ]]; then continue; fi
    f=$OUT/${c}_n${n}.csv; [ -f $f ] || python3 run_special.py $c $n $REPS 9 $f 2
  done
done
echo "HUTIAN_WAKE: special grid finished"
