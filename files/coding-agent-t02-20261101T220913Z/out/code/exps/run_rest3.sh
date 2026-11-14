#!/bin/bash
cd /work/code
/work/venv/bin/python /work/exps/e3_capacity.py > /work/results/e3_capacity_b.log 2>&1
/work/venv/bin/python /work/exps/e4_arch.py > /work/results/e4_arch_b.log 2>&1
