#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
RESEARCH_PYTHON="${RESEARCH_PYTHON:-$PWD/.venv/bin/python}"
mkdir -p logs
"$RESEARCH_PYTHON" -m unittest discover -s src -p 'test_*.py' -v > logs/tests.log 2>&1
"$RESEARCH_PYTHON" src/run_experiments.py --reps 100 --workers 4 > logs/reproduction_run.log 2>&1
"$RESEARCH_PYTHON" src/analyze.py > logs/analysis.log 2>&1
"$RESEARCH_PYTHON" src/check_numerics.py > logs/numerical_checks.log 2>&1
latexmk -cd -pdf -interaction=nonstopmode -halt-on-error paper/main.tex > logs/latex.log 2>&1
cp paper/main.pdf paper.pdf
"$RESEARCH_PYTHON" src/validate_artifact.py > logs/artifact_validation.log 2>&1
echo 'Reproduction complete: paper.pdf and results/.'
