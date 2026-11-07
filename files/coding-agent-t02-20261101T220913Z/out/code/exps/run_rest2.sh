#!/bin/bash
cd /work/code
while pgrep -f "run_rest.s[h]" > /dev/null; do sleep 20; done
/work/venv/bin/python /work/exps/e3_capacity.py > /work/results/e3_capacity_b.log 2>&1
