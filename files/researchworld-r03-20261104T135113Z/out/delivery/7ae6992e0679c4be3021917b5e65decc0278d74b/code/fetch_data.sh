#!/usr/bin/env bash
# Download the pinned public sources into $DATA (default /hutian/data). ~3.3 GB (MTEB checkout), others < 5 MB.
set -euo pipefail
DATA=${DATA:-/hutian/data}
mkdir -p $DATA/mteb $DATA/olb $DATA/livebench $DATA/helm
# MTEB results @ 6dabbcc68c28ea5f180ce7df79347b3ca9cc6383 (2026-03-31), CC0-1.0
cd $DATA/mteb && git init -q . && git remote add origin https://github.com/embeddings-benchmark/results || true
git fetch -q --depth 1 origin 6dabbcc68c28ea5f180ce7df79347b3ca9cc6383 && git checkout -q FETCH_HEAD
# Open LLM Leaderboard contents @ 9c09a7cae43334062a82cb164f2ef255013dafa2
curl -fsSL -o $DATA/olb/contents.parquet "https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet"
# LiveBench model_judgment @ 9704e5da7bfbefe75ac1482a13de827127295993
curl -fsSL -o $DATA/livebench/judgment.parquet "https://huggingface.co/datasets/livebench/model_judgment/resolve/9704e5da7bfbefe75ac1482a13de827127295993/data/leaderboard-00000-of-00001.parquet"
# HELM Lite v1.13.0
curl -fsSL -o $DATA/helm/core_scenarios.json "https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output/releases/v1.13.0/groups/core_scenarios.json"
# HELM MMLU subjects, release v1.13.0 of the HELM MMLU project (additional public source; licence not verified)
curl -fsSL -o $DATA/helm/mmlu_subjects_v1.13.0.json "https://storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/groups/mmlu_subjects.json"
# HELM Lite v1.13.0 per-subset groups (extended HELM-Lite matrix helm_lite_ext; build_helm_ext.py)
mkdir -p $DATA/helm/lite_groups
for g in legalbench math_chain_of_thought wmt_14 mmlu; do
  curl -fsSL -o $DATA/helm/lite_groups/$g.json "https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output/releases/v1.13.0/groups/$g.json"
done
