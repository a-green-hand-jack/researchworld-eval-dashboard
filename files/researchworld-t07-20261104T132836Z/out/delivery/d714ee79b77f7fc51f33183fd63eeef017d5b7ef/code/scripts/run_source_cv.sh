#!/usr/bin/env bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$(dirname "$0")/.."; mkdir -p results/source_cv
for b in $1; do python3 -I src/source_cv.py $b results/source_cv/$b.csv; echo done $b; done
