#!/usr/bin/env bash
# usage: make_tables.sh "bench,bench,..."   (per-benchmark tables -> results/cells/); then: python3 -I src/merge_tables.py results results/raw/main results/raw/m2 results/raw/m4 results/raw/ablate
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$(dirname "$0")/.."
BENCH=$1 python3 -I src/make_tables.py results results/raw/main results/raw/m2 results/raw/m4 results/raw/ablate
