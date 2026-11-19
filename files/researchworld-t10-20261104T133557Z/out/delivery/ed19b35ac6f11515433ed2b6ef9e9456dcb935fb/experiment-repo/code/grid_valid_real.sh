#!/bin/bash
# Finite-sample validity grid: Wald vs t vs studentised bootstrap, no learners (cheap). Raw rows -> $OUT.
export PYTHONWARNINGS=ignore OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
OUT=${OUT:-/hutian/scratch/raw/valid_real}; REPS=${REPS:-2000}; mkdir -p $OUT
cd "$(dirname "$0")"
for d in forest galaxies alphafold gene_expression census_income census_healthcare census_education; do
  for n in 15 25 50 100 200 500; do
    [ -f $OUT/${d}_n${n}.csv ] || BOOT=1 python3 run_real.py $d $n $REPS 5 $OUT/${d}_n${n}.csv 20000 2 ""
  done
done
echo "HUTIAN_WAKE: validity grid finished"
