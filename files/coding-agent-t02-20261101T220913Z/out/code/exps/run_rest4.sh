#!/bin/bash
cd /work/code
while pgrep -f "run_rest3.s[h]" > /dev/null; do sleep 30; done
/work/venv/bin/python /work/exps/e6_ops.py > /work/results/e6_ops.log 2>&1
