#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$project_root"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
if [[ "${AUDIT_SKIP_INSTALL:-0}" != 1 ]]; then .venv/bin/python -m pip install -r requirements.txt; fi
mkdir -p results figures paper/generated
.venv/bin/python src/download.py
.venv/bin/python src/prepare.py
.venv/bin/python src/test_core.py | tee results/core_checks.log
.venv/bin/python src/experiment.py > results/experiment.log 2>&1
.venv/bin/python src/controls.py > results/controls.log 2>&1
.venv/bin/python src/uncertainty.py > results/uncertainty.log
.venv/bin/python src/report.py > results/report.log
(cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex) > results/latex_build.log 2>&1
cp paper/main.pdf paper.pdf
.venv/bin/python src/verify.py
