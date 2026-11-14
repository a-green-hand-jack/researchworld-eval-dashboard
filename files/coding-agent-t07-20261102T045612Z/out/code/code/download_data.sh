#!/bin/sh
# Download the pinned data files (commit 55faff496947789f94e6b5908c77cbc3e84f81ad of socialfoundations/benchmark-prediction, MIT).
# Usage: sh code/download_data.sh /work/data_raw     (the files are untrusted pickles: they are only read by prep_data.py's restricted unpickler)
set -e
OUT=${1:-/work/data_raw}; mkdir -p "$OUT"; cd "$OUT"
C=55faff496947789f94e6b5908c77cbc3e84f81ad
B=https://raw.githubusercontent.com/socialfoundations/benchmark-prediction/$C/data
for f in arc_challenge bbh gpqa ifeval mmlu_pro musr openllm_math commonsense gsm legalbench math med_qa mmlu; do curl -sSfO $B/scores/$f.jbl; done
for f in arc_challenge bbh gpqa ifeval mmlu_pro musr openllm_math; do curl -sSfO $B/scores/${f}_models.jbl; done
curl -sSfO $B/openllm_model_list.txt; curl -sSfO $B/helm_model_list.txt
