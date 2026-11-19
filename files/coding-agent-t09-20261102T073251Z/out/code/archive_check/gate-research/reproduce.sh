#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export PYTHONHASHSEED=0
task_python="${TASK_PYTHON:-.venv/bin/python}"
mkdir -p logs results figures paper/generated
"$task_python" code/fetch_data.py
"$task_python" code/verify.py > logs/verify.json
for mode in main noise scaling validation saturation sensitivity; do
    reps=400
    if [[ "$mode" == "validation" ]]; then reps=150; fi
    "$task_python" code/study.py --mode "$mode" --reps "$reps" > "logs/$mode.log" 2>&1
done
"$task_python" code/support_ablation.py > logs/support.log 2>&1
"$task_python" code/analyze.py > logs/analyze.log 2>&1
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex > logs/latex.log 2>&1
"$task_python" code/audit.py > logs/audit.json
echo 'Reproduced paper/main.pdf and all reported tables/figures.'
