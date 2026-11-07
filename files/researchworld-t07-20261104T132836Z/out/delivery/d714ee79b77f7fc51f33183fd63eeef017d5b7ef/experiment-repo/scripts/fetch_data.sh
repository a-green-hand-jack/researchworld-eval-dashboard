#!/usr/bin/env bash
# Download the pinned score matrices (benchmark-prediction @ 55faff49, MIT) into $DATA (default /hutian/data/raw).
set -euo pipefail
DATA=${DATA:-/hutian/data/raw}; C=55faff496947789f94e6b5908c77cbc3e84f81ad
B=https://raw.githubusercontent.com/socialfoundations/benchmark-prediction/$C/data
mkdir -p "$DATA"; cd "$DATA"
for f in arc_challenge bbh gpqa ifeval mmlu_pro musr openllm_math commonsense gsm legalbench math med_qa mmlu; do
  curl -fsSL -O $B/scores/$f.jbl; done
for f in arc_challenge bbh gpqa ifeval mmlu_pro musr openllm_math; do curl -fsSL -O $B/scores/${f}_models.jbl; done
for f in openllm_model_list helm_model_list; do curl -fsSL -O $B/$f.txt; done
sha256sum *.jbl *.txt > SHA256SUMS
