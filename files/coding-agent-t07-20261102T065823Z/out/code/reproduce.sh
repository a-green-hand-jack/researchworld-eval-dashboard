#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PYTHON_RUN="${PYTHON_RUN:-.venv/bin/python}"
"$PYTHON_RUN" src/download_data.py
"$PYTHON_RUN" src/common.py
"$PYTHON_RUN" src/test_design.py
"$PYTHON_RUN" src/run_experiments.py --jobs 4
"$PYTHON_RUN" src/augment_results.py --jobs 4
"$PYTHON_RUN" src/run_diagnostics.py --jobs 4
"$PYTHON_RUN" src/report.py
"$PYTHON_RUN" src/fill_checklist.py
bash build.sh
"$PYTHON_RUN" src/validate_outputs.py
