#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export OPENBLAS_NUM_THREADS=1
.venv/bin/python src/test_core.py
.venv/bin/python src/analyze.py --mode all --repetitions 4000
.venv/bin/python src/render.py
bash src/build_paper.sh
