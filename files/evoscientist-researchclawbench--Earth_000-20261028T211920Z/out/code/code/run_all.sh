#!/bin/sh
# Reproduce the full analysis from the workspace root:  sh code/run_all.sh
set -e
pip install -q pandas numpy matplotlib pymupdf
python code/01_inventory.py      > outputs/inventory.log
python code/02_run_main.py       > outputs/run_main.log
python code/03_compare_official.py > outputs/compare_official.log
python code/04_validation.py     > outputs/validation.log
python code/05_figures.py
python code/06_extra_stats.py    > outputs/extra_stats.log
echo done
python code/07_tables_md.py > outputs/tables.log
