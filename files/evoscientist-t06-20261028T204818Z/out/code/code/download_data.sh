#!/usr/bin/env bash
# Download all raw data used in the paper into ./data (run from repository root).
# All URLs are pinned to fixed commits; checksums are verified afterwards by code/verify_data.py.
set -euo pipefail
mkdir -p data/mtbench data/arena55k data/arena140k data/nba data/arena_judges/llm-judges-prob-avg
HF=https://huggingface.co/datasets

# 1) MT-Bench human & GPT-4 pairwise judgments (expert annotators + model judge)
C=f7d2896d2cc5d80f8b55c2bbc722613555233c25
curl -sSL -o data/mtbench/human.parquet "$HF/lmsys/mt_bench_human_judgments/resolve/$C/data/human-00000-of-00001-25f4910818759289.parquet"
curl -sSL -o data/mtbench/gpt4_pair.parquet "$HF/lmsys/mt_bench_human_judgments/resolve/$C/data/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet"

# 2) Chatbot Arena human preference 55k (crowdsourced votes, 2023-2024)
C=18c298340948c0e7f7727399fd459cca6ce0ca6f
curl -sSL -o data/arena55k/train.csv "$HF/lmarena-ai/arena-human-preference-55k/resolve/$C/train.csv"

# 3) NBA game records (sports)
G=4c1ff5e3aef1816ae04af63218015066e186c147
curl -sSL -o data/nba/nbaallelo.csv "https://raw.githubusercontent.com/fivethirtyeight/data/$G/nba-elo/nbaallelo.csv"

# 4) LLM-judge verdicts on Arena battles (model judges on the same battles as crowd votes)
C=638a7e3be3078e55d2eb0b789d34749747822c49
curl -sSL -o data/arena_judges/train.single-turn.json "$HF/potsawee/chatbot-arena-llm-judges/resolve/$C/train.single-turn.json"
for J in Qwen2-72B-Instruct Meta-Llama-3-70B-Instruct Meta-Llama-3-8B-Instruct Mistral-7B-Instruct-v0.2 Athene-70B; do
  curl -sSL -o "data/arena_judges/llm-judges-prob-avg/$J.jsonl" "$HF/potsawee/chatbot-arena-llm-judges/resolve/$C/llm-judges-prob-avg/$J.jsonl"
done

# 5) Chatbot Arena human preference 140k (crowdsourced votes, 2025), 7 parquet shards
C=6322995ab34d7c2693e3f47dd13fa5caa0789a74
for i in 0 1 2 3 4 5 6; do
  curl -sSL -o "data/arena140k/train-0000$i-of-00007.parquet" "$HF/lmarena-ai/arena-human-preference-140k/resolve/$C/data/train-0000$i-of-00007.parquet"
done
echo "download done"
