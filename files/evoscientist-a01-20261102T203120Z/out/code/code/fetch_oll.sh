#!/bin/sh
# Fetch the Open LLM Leaderboard snapshots used in the paper (pinned commits). Run from repo root.
set -e
mkdir -p data
# 1) aggregated table (single parquet, ~1.1 MB); commit 9c09a7cae43334062a82cb164f2ef255013dafa2 (2025-03-20)
curl -sL -o data/contents.parquet \
  https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet
echo "f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5  data/contents.parquet" | sha256sum -c -
# 2) per-run result JSONs (~1.3 GB incl. git metadata); commit aa81ecc38fdc5708254b833923368970efdf5ef5 (2025-03-15)
if [ ! -d data/oll_results ]; then
  git clone -q https://huggingface.co/datasets/open-llm-leaderboard/results data/oll_results
fi
git -C data/oll_results checkout -q aa81ecc38fdc5708254b833923368970efdf5ef5
git -C data/oll_results rev-parse HEAD
