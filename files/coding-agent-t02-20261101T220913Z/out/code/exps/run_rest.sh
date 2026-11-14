#!/bin/bash
cd /work/code
while pgrep -f "exps/e2_cloc[k]" > /dev/null; do sleep 20; done
for e in e3_capacity e5_rescale e4_arch; do
  /work/venv/bin/python /work/exps/$e.py > /work/results/$e.log 2>&1
done
