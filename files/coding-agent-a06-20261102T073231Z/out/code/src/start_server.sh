#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo $$ > logs/server.pid
exec vendor/llama.cpp/build/bin/llama-server \
  --model data/model.gguf --host 127.0.0.1 --port 8080 \
  --ctx-size 65536 --parallel 8 --threads 4 --threads-batch 4 \
  --batch-size 2048 --ubatch-size 512 --no-warmup \
  --metrics --log-disable
