#!/bin/bash
# Full reproduction (about 45-60 core-hours; ~12-15 h wall on 4 cores). Resumable: finished runs are skipped.
set -e
cd "$(dirname "$0")/code"
PY=${PY:-python3}
for e in e1_width e2_clock e3_capacity e4_arch e5_rescale e6_ops; do $PY ../exps/$e.py; done
for f in fig_e1 fig_e2 fig_e3 fig_e4 fig_e5 fig_e6; do $PY -W ignore $f.py; done
$PY make_tables.py; $PY cost.py
cd ../paper && latexmk -pdf main.tex
