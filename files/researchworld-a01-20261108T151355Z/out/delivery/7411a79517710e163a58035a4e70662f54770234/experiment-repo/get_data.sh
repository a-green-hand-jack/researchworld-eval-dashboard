#!/bin/bash
# Raw-data acquisition and rebuild of data/processed (needs network). Usage: ./get_data.sh [RAWDIR]   (default: ./raw, kept outside version control)
#   1. Open LLM Leaderboard `contents` table, dataset commit 9c09a7cae43334062a82cb164f2ef255013dafa2 (one parquet file, 4576 rows)
#   2. one pinned lm-eval results file of the Open LLM Leaderboard `results` dataset, commit aa81ecc38fdc5708254b833923368970efdf5ef5 (item counts per task for the noise model)
#   3. HELM MMLU v1.13.0 release summaries from the public bucket gs://crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/ (303 files; per-file SHA-256 in the manifest src/fetch_helm.py writes)
# Each raw file is checked against data/raw_checksums.sha256; the rebuilt tables against data/processed/CHECKSUMS.sha256 (they are byte-identical to the shipped ones).
set -e; cd "$(dirname "$0")"; RAW=${1:-raw}; mkdir -p "$RAW/ollb" "$RAW/ollb_results" "$RAW/helm"
curl -fL -o "$RAW/ollb/train-00000-of-00001.parquet" \
  "https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet"
curl -fL -o "$RAW/ollb_results/results_2024-08-07T13-21-02.903091.json" \
  "https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/aa81ecc38fdc5708254b833923368970efdf5ef5/0-hero/Matter-0.2-7B-DPO/results_2024-08-07T13-21-02.903091.json"
python3 src/fetch_helm.py "$RAW/helm/v1.13.0"
(cd "$RAW" && sha256sum -c "$OLDPWD/data/raw_checksums.sha256")
python3 src/build_data.py "$RAW/ollb/train-00000-of-00001.parquet" "$RAW/helm/v1.13.0" data/processed
python3 src/ollb_items.py data/processed/ollb_noise.json          # downloads the same pinned results file; its SHA-256 is stored in ollb_noise.json
(cd data/processed && sha256sum -c CHECKSUMS.sha256)
