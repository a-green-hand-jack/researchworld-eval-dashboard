#!/bin/sh
cd /work/code
/work/venv/bin/python -I exp2_boot.py main 200 > /work/results/exp2main.log 2>&1
/work/venv/bin/python -I exp2_boot.py judges 100 > /work/results/exp2j.log 2>&1
/work/venv/bin/python -I exp2_boot.py nba 100 > /work/results/exp2n.log 2>&1
