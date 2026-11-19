#!/bin/bash
# Reproduce every simulation in the paper: E1-E4, 500 replications per setting.
# Runtime on 38 CPU workers was about 1 h in total (see README.md).
set -e
cd /work/code
for e in E1 E2 E3 E4; do
  /work/venv/bin/python run_sim.py --exp $e --reps 500 --workers 38
done
