#!/bin/bash
# Fetch the public inputs (no network is needed afterwards) and build the processed score matrices.
# Run from the repository root:  bash code/fetch_data.sh        (~5 min, ~15 MB HELM + 4.5 MB OLB contents + ~80 MB OLB results subset)
set -euo pipefail
cd "$(dirname "$0")/.."
bash code/fetch_helm.sh data/helm_v1.13.0_filelist.txt                       # HELM MMLU v1.13.0 summary files (GCS, crfm-helm-public)
mkdir -p data/raw/olb_contents
curl -fsSL -o data/raw/olb_contents/train-00000-of-00001.parquet \
  "https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet"
echo "f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5  data/raw/olb_contents/train-00000-of-00001.parquet" | sha256sum -c -
python3 code/analysis/01_build_data.py                                       # data/processed/{helm_mmlu_v1.13.0,helm_mmlu_neval,olb_contents}.csv + manifest.json
python3 code/analysis/01b_fetch_olb_results.py                               # bounded OLB `results` subset -> olb_subtask.csv (needs the HF API)
