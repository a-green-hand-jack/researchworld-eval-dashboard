#!/usr/bin/env bash
# Download the public raw data (fixed snapshots) into data/.  ~2 GB.
set -euo pipefail
cd "$(dirname "$0")"
HF=https://huggingface.co/datasets
mkdir -p data/arena55k data/arena140k data/webdev data/mtbench data/judges/llm-judges data/judges/llm-judges-reversed data/nba
curl -sL -o data/arena55k/train.csv $HF/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv
for i in 0 1 2 3 4 5 6; do
  curl -sL -o data/arena140k/train-0000$i.parquet $HF/lmarena-ai/arena-human-preference-140k/resolve/6322995ab34d7c2693e3f47dd13fa5caa0789a74/data/train-0000$i-of-00007.parquet
done
curl -sL -o data/webdev/webdev-arena-preference-10k.json $HF/lmarena-ai/webdev-arena-preference-10k/resolve/7c397e652ffb8c2384e6d71d21d8388c19365fdc/data/webdev-arena-preference-10k.json
MT=$HF/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/data
curl -sL -o data/mtbench/human.parquet $MT/human-00000-of-00001-25f4910818759289.parquet
curl -sL -o data/mtbench/gpt4_pair.parquet $MT/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet
J=$HF/potsawee/chatbot-arena-llm-judges/resolve/638a7e3be3078e55d2eb0b789d34749747822c49
curl -sL -o data/judges/train.single-turn.json $J/train.single-turn.json
for j in Qwen2-72B-Instruct Meta-Llama-3-70B-Instruct Athene-70B Meta-Llama-3-8B-Instruct Mistral-7B-Instruct-v0.1; do
  curl -sL -o data/judges/llm-judges/$j.jsonl $J/llm-judges/$j.jsonl
  curl -sL -o data/judges/llm-judges-reversed/$j.jsonl $J/llm-judges-reversed/$j.jsonl
done
curl -sL -o data/nba/nbaallelo.csv https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv
sha256sum -c SHA256SUMS
