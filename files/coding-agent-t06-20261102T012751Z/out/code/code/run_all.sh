#!/bin/sh
# Full pipeline (about 45 min on 38 CPU cores).  Usage: cd /work/code && sh run_all.sh
# Requires data in /work/data (see README.md), venv in /work/venv.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=../venv/bin/python
mkdir -p ../results
$PY exp_validate.py   > ../results/validate.log 2>&1   # validation of search, se check        (~15 s)
$PY exp_main.py       > ../results/main.log 2>&1       # all pairs, all boards                 (~6 min)
$PY exp_random.py     > ../results/random.log 2>&1     # random-edit baseline                  (~1 min)
$PY exp_boot.py       > ../results/boot.log 2>&1       # vote-bootstrap replicates             (~25 min)
$PY exp_judges.py     > ../results/judges.log 2>&1     # same battles, LLM judges              (~13 min)
$PY exp_control.py    > ../results/control.log 2>&1    # matched six models, sample size       (~10 min)
$PY exp_sigcheck.py   > ../results/sigcheck.log 2>&1   # significance witnesses re-check       (~1 min)
$PY exp_baselines.py  > ../results/baselines.log 2>&1  # search-strategy baselines             (~2 min)
$PY exp_cluster.py    > ../results/cluster.log 2>&1    # question-level deletion, MT-Bench     (~1 min)
$PY exp_arena140k.py  > ../results/arena140k.log 2>&1  # Arena-140k replication, sessions, temporal split (~12 min)
$PY exp_temporal.py   > ../results/temporal.log 2>&1   # temporal vs random split, Arena-140k (~3 min)
$PY exp_ablate.py     > ../results/ablate.log 2>&1     # ridge ablation                        (~1 min)
$PY analysis.py       > ../results/analysis.log 2>&1   # tables, figures, number macros
