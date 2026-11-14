#!/bin/sh
# runs all experiments sequentially (each uses a 36-process pool)
cd "$(dirname "$0")"
for e in "$@"; do ../venv/bin/python experiments.py $e > ../results/$e.log 2>&1; done
