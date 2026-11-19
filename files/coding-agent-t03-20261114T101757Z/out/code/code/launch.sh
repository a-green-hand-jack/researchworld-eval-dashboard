#!/bin/sh
# Launch sweeps with single-threaded BLAS/OpenMP (avoids thread oversubscription).
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /work/code
case "$1" in
  main) /work/venv/bin/python -W ignore explain.py 16 main > /work/results/logs/main.log 2>&1 ;;
  exact) cat /work/results/logs/exact_jobs_rem.txt | xargs -P 2 -L 1 /work/venv/bin/python -W ignore exact.py > /work/results/logs/exact2.log 2>&1 ;;
esac
