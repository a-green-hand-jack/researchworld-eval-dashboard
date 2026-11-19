#!/bin/bash
# Full pipeline for the paper. Runs sequentially: the container has a 4-CPU quota.
set -e
cd /work/code
export PYTHONUNBUFFERED=1
PY=/work/venv/bin/python
$PY tests/test_identities.py
$PY run_synth.py --stage main --reps 500 --procs 6 --out /work/results/synth_main.csv
$PY run_real.py  --stage main --reps 300 --procs 6 --out /work/results/real_main.csv
$PY theory_pool.py
$PY theory_check.py
$PY summarize.py /work/results/synth_main.csv /work/results/synth_main
$PY summarize.py /work/results/real_main.csv /work/results/real_main
CFG=$($PY -c "from run_real import CONFIGS; print(' '.join(str(i) for i,c in enumerate(CONFIGS) if c in [('forest','f'),('alphafold','f'),('gene_expression','f'),('census_education','fX')]))")
$PY run_real.py --stage main --reps 100 --procs 6 --ns 5000 20000 --ratios 4 --configs $CFG --out /work/results/real_largen.csv
$PY make_tables.py
$PY make_figures.py
echo DONE
