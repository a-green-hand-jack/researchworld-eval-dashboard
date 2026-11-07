#!/bin/bash
. /work/venv/bin/activate; cd /work/code
python -u exp_real_main.py 4 400 > /work/logs/real_main.log 2>&1
python -u exp_conclusions.py real 4 300 > /work/logs/concl_real.log 2>&1
python -u exp_permnull.py /work/cache/q15 300 > /work/logs/permnull.log 2>&1
