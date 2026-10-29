#!/bin/sh
# Downloads the pinned public data to ${RSENS_DATA:-/hutian/data} and verifies sha256 (values from the task's data.md). ~200 MB.
set -e; D=${RSENS_DATA:-/hutian/data}; mkdir -p "$D"; cd "$D"
H=https://huggingface.co/datasets
curl -fsSL -o arena55k_train.csv $H/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv
V=$H/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/data
curl -fsSL -o mtbench_human.parquet $V/human-00000-of-00001-25f4910818759289.parquet
curl -fsSL -o mtbench_gpt4pair.parquet $V/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet
curl -fsSL -o nbaallelo.csv https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv
sha256sum -c <<EOF
0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2  arena55k_train.csv
4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769  mtbench_human.parquet
57068327ffb5f8fddb15fedbbfe40b26fe862da2326331e5cf64a42320a00e71  mtbench_gpt4pair.parquet
d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc  nbaallelo.csv
EOF
