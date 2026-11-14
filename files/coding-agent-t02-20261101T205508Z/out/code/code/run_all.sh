#!/bin/bash
# Runs all experiments sequentially (each uses 4 worker processes). Expected ~ 1 day on 4 cores.
cd /work/code
for e in e1_mlp_width e2_tf_width e3_frac e4_randlabel e5_hparam e6_tasks e7_init e8_depth; do
  ../venv/bin/python sweep.py $e 4 > ../results/$e.log 2>&1
done
