#!/usr/bin/env bash
# Reproduces every table and figure of the paper. Run from /work/code with the virtualenv at /work/venv (see README).
# Approximate wall-clock on 4 effective CPU cores: ~2.5 h total (about 10 CPU-hours).
set -e
PY=../venv/bin/python
export PATH=$(dirname $PY):$PATH          # gdown must be on PATH for ppi_py's data download
mkdir -p ../data ../results ../figs ../paper/tables
(cd ../data && $PY -I -c "
from ppi_py.datasets import load_dataset
for n in ['galaxies','forest','alphafold','gene_expression','census_income','census_healthcare','census_education','plankton','ballots']: load_dataset('/work/data/', n)")
$PY -I theory.py                      # population-level bounds -> results/theory_*.csv   (~1 min)
$PY -I pop_stats.py                   # in-sample population statistics -> results/pop_stats.json (not used in tables; sanity check)
for e in E3a E3b E3c E3d E4; do $PY -I run_experiments.py $e --reps 2000 --procs 4; done   # ~1.1 h
for e in E2 E1b E1a; do $PY -I run_experiments.py $e --reps 1000 --procs 4; done           # ~1.1 h
$PY -I application.py                 # ballots, results/E5_ballots.csv (seconds)
$PY -I xgain.py                       # census side-information check, results/xgain.csv (~30 s)
$PY -I summarize.py E1a E1b E2 E3a E3b E3c E3d E4
$PY -I make_tables.py                 # paper/tables/*.tex
$PY -I make_figures.py                # figs/*.pdf
$PY -I paper_numbers.py > ../results/paper_numbers.txt   # numbers quoted in the text for E3a/c/d
