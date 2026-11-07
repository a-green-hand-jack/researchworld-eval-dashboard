#!/bin/bash
# Full pipeline after get_data.sh: synthetic experiments, real-data experiments, tables+figures. ~1 h wall-clock on 40 cores.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
PY=/work/venv/bin/python
cd /work/code; mkdir -p /work/out/logs /work/out/results /work/out/synth /work/paper
for e in 1 2 3 4 5 6; do $PY run_synth.py $e > /work/out/logs/synth_$e.log 2>&1 & done
./run_all_real.sh > /work/out/run_all.log 2>&1       # real-data experiments (MTEB/OpenLLM/HELM/LiveBench + conditions)
$PY run_bias.py helm_fine > /work/out/logs/bias_helm_fine.log 2>&1
$PY run_bias.py mteb_main > /work/out/logs/bias_mteb_main.log 2>&1
wait
$PY make_results.py > /work/out/logs/make_results.log 2>&1
