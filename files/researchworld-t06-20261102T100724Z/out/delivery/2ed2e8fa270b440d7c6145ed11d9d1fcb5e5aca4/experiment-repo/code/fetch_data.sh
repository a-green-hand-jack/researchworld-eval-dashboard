#!/bin/sh
# Download the pinned public inputs into $DATA_DIR (default /hutian/data) and verify their sha256.
# Usage: sh fetch_data.sh [--judges]    (--judges also fetches the optional crowd-vs-LLM-judge files)
set -eu
D="${DATA_DIR:-/hutian/data}"
HF=https://huggingface.co/datasets
get() {  # url dest sha256
  mkdir -p "$(dirname "$2")"
  [ -f "$2" ] || curl -fL --retry 3 -o "$2" "$1"
  echo "$3  $2" | sha256sum -c -
}
get $HF/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv \
    "$D/arena55k/train.csv" 0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2
get $HF/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/data/human-00000-of-00001-25f4910818759289.parquet \
    "$D/mtbench/human-00000-of-00001-25f4910818759289.parquet" 4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769
get $HF/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/data/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet \
    "$D/mtbench/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet" 57068327ffb5f8fddb15fedbbfe40b26fe862da2326331e5cf64a42320a00e71
get https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv \
    "$D/nba/nbaallelo.csv" d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc
if [ "${1:-}" = "--judges" ]; then
  J=$HF/potsawee/chatbot-arena-llm-judges/resolve/638a7e3be3078e55d2eb0b789d34749747822c49
  get $J/train.single-turn.json "$D/judges/train.single-turn.json" 6ed8793f61931637b65c1f348e8cb3a050996eef2a8c5c37c0b42fcfe465c8f3
  get $J/llm-judges-prob-avg/Meta-Llama-3-70B-Instruct.jsonl "$D/judges/Meta-Llama-3-70B-Instruct.avg.jsonl" 6a89941a437911fea0f724955092718af43c07242e9d54937303834014c86ff8
  get $J/llm-judges-prob-avg/Athene-70B.jsonl "$D/judges/Athene-70B.avg.jsonl" dd6b1925ef6f2f5f5fa24799c57070ed23e587cef050784107b7251b69394b91
  get $J/llm-judges-prob-avg/Qwen2-72B-Instruct.jsonl "$D/judges/Qwen2-72B-Instruct.avg.jsonl" bffcf2d5ff16de26db64a57be3c66f51d2889a2063490976a6ac0423b8b31aec
fi
