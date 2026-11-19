#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
bash analysis/scripts/finalize_confirmatory.sh
python3 analysis/postprocess/study_summaries.py --input analysis/results/confirmatory/trials.jsonl --summary analysis/results/confirmatory/summary --config analysis/configs/frozen.json --output analysis/results/confirmatory/derived
python3 analysis/postprocess/audit_final.py --root analysis/results/confirmatory --config analysis/configs/frozen.json --output analysis/results/confirmatory/final_audit.json --source-mode files
echo 'HUTIAN_WAKE: full 1900-trial aggregation, uncertainty, sensitivity and numerical-policy audit completed'
