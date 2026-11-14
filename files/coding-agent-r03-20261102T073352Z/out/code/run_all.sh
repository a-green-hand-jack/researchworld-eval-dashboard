#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1
study_python="${STUDY_PYTHON:-.venv/bin/python}"
mkdir -p data/raw data/processed results figures logs paper/generated
"$study_python" scripts/prepare.py > logs/prepare.log 2>&1
"$study_python" scripts/core.py
"$study_python" scripts/test_invariants.py > logs/tests.log 2>&1
for study_dataset in mteb openllm mteb_core; do
  for study_protocol in random publisher; do
    "$study_python" scripts/experiment.py --dataset "$study_dataset" --protocol "$study_protocol" > "logs/${study_dataset}_${study_protocol}_main.log" 2>&1
  done
done
"$study_python" scripts/experiment.py --dataset mteb_modal --protocol random > logs/mteb_modal_random_main.log 2>&1
"$study_python" scripts/experiment.py --dataset mteb --audit fixed > logs/mteb_random_fixed.log 2>&1
"$study_python" scripts/experiment.py --dataset mteb --audit missing > logs/mteb_random_missing.log 2>&1
"$study_python" scripts/experiment.py --dataset openllm --audit fixed > logs/openllm_random_fixed.log 2>&1
"$study_python" scripts/experiment.py --dataset openllm --protocol temporal > logs/openllm_temporal_main.log 2>&1
"$study_python" scripts/fixed_all.py > logs/openllm_random_fixedall.log 2>&1
"$study_python" scripts/budget_baseline.py > logs/budget_baseline.log 2>&1
"$study_python" scripts/theory.py > logs/theory.log 2>&1
"$study_python" scripts/report.py > logs/report.log 2>&1
make -C paper > logs/latex.log 2>&1
"$study_python" scripts/audit.py > logs/audit.log 2>&1
