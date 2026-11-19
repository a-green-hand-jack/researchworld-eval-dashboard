#!/bin/bash
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
python3 -I exp/e8_sweep.py A2 results/E8 --Ms 20,30,45,60,90,100 --masks 0,0.25,0.5 --reps 10 --ntest 25
python3 -I exp/e8_sweep.py A1 results/E8 --Ms 20,30,45,60,78 --masks 0,0.25,0.5 --reps 10 --ntest 25
python3 -I exp/e8_sweep.py OLMB6 results/E8 --Ms 30,60,125,500,2000 --masks 0 --reps 5 --ks 1,2,3,4 
python3 -I exp/e8_sweep.py OLMB40 results/E8 --Ms 30,60,125,500,2000 --masks 0,0.5 --reps 5 --n_random 20
echo "HUTIAN_WAKE: e8 finished"
