#!/bin/bash
# Download the pinned public data into /work/data (each source in its own directory; ~3.4 GB for the MTEB clone).
set -e
D=/work/data; mkdir -p $D/mteb_raw $D/openllm $D/helm $D/livebench
# --- MTEB results (CC0-1.0), pinned commit
cd $D/mteb_raw && git clone --quiet https://github.com/embeddings-benchmark/results.git repo
cd repo && git checkout --quiet 6dabbcc68c28ea5f180ce7df79347b3ca9cc6383
# --- Open LLM Leaderboard contents (pinned dataset commit)
curl -s -L -o $D/openllm/contents.parquet "https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet"
# --- HELM Lite v1.13.0 group files
B=https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output/releases/v1.13.0
curl -s -L -o $D/helm/core_scenarios.json $B/groups/core_scenarios.json
for g in mmlu legalbench wmt_14; do curl -s -L -o $D/helm/g_$g.json $B/groups/$g.json; done
# --- LiveBench model_judgment (pinned dataset commit)
curl -s -L -o $D/livebench/judgment.parquet "https://huggingface.co/datasets/livebench/model_judgment/resolve/9704e5da7bfbefe75ac1482a13de827127295993/data/leaderboard-00000-of-00001.parquet"
# --- MTEB matrix + task metadata (needs `pip install mteb==2.26.31` in a separate venv; metadata only)
cd /work/code
python -I extract_mteb.py $D/mteb_raw/repo/results $D/mteb_proc
# python mteb_task_meta.py $D/mteb_proc/mteb_task_meta.csv      # run with the venv that has mteb installed
python -I prep_data.py
