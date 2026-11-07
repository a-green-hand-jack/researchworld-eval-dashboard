#!/usr/bin/env bash
# Run from the workspace root. Existing exact-success training commands resume.
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest test_train.py test_analysis.py test_launcher.py -q
if [[ "${1:-full}" != "--analysis-only" ]]; then
  python run_jobs.py confirm_jobs.json --workers "${WORKERS:-8}"
fi
python analyze.py
python stability.py
python verify_constructive.py
python plot.py
python export_tex.py
latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex
python verify_artifacts.py --checkpoints --paper
