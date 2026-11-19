#!/bin/bash
# Runs all real-data experiments (about 2-3 CPU-hours in total on 40 cores, ~45 min wall-clock). Output: /work/out/results
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
PY=/work/venv/bin/python
cd /work/code
mkdir -p /work/out/results /work/out/logs
$PY run_real.py mteb_main rand --repeats 3 --procs 15 > /work/out/logs/mteb_main_rand.log 2>&1 &
$PY run_real.py mteb_main org --procs 5 > /work/out/logs/mteb_main_org.log 2>&1 &
$PY run_real.py mteb_main time --procs 1 > /work/out/logs/mteb_main_time.log 2>&1 &
$PY run_real.py mteb_dense rand --repeats 3 --procs 15 > /work/out/logs/mteb_dense_rand.log 2>&1 &
wait
$PY run_real.py mteb_eng rand --repeats 3 --procs 15 > /work/out/logs/mteb_eng_rand.log 2>&1 &
$PY run_real.py openllm rand --repeats 1 --procs 5 > /work/out/logs/openllm_rand.log 2>&1 &
$PY run_real.py openllm time --procs 1 > /work/out/logs/openllm_time.log 2>&1 &
$PY run_real.py helm_fine rand --repeats 10 --procs 20 > /work/out/logs/helm_fine_rand.log 2>&1 &
$PY run_real.py helm_core10 rand --repeats 10 --procs 20 > /work/out/logs/helm_core10_rand.log 2>&1 &
$PY run_real.py livebench rand --repeats 10 --procs 20 > /work/out/logs/livebench_rand.log 2>&1 &
wait
$PY run_conditions.py --procs 38 > /work/out/logs/conditions.log 2>&1
echo ALLDONE > /work/out/logs/done.txt
