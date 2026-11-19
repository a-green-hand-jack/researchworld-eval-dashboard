#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python "$ROOT/src/download.py"
python "$ROOT/src/prepare.py"
python -m pytest -q "$ROOT/tests"
python "$ROOT/src/run.py" --repeats 100 --bootstrap 200
python "$ROOT/src/supplement.py"
python "$ROOT/src/report.py"
python "$ROOT/src/validate.py"
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd "$ROOT/paper/main.tex"
cp "$ROOT/paper/main.pdf" "$ROOT/paper.pdf"
