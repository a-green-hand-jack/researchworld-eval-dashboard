#!/bin/sh
# Full pipeline. Expected cost: roughly 15-25 CPU-hours (see README); resumable (finished cells are skipped).
set -e
python3 src/prepare.py
for s in E1 E4 E3 E2 E5; do python3 src/run_main.py $s ${NJOBS:-40}; done
python3 src/validate_reference.py
python3 src/build_tables.py E1 E2 E3 E4 E5
python3 src/analyze.py
