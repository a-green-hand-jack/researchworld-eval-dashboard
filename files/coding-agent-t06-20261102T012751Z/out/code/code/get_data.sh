#!/bin/sh
# Downloads the public data used in the paper into /work/data (one directory per source) and verifies checksums.
set -e
D=/work/data
mkdir -p $D/arena55k $D/arena140k $D/mtbench $D/nba $D/judges/llm-judges-prob-avg
HF=https://huggingface.co/datasets
curl -sL -o $D/arena55k/train.csv $HF/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv
for i in 0 1 2 3 4 5 6; do
  curl -sL -o $D/arena140k/train-0000$i-of-00007.parquet $HF/lmarena-ai/arena-human-preference-140k/resolve/6322995ab34d7c2693e3f47dd13fa5caa0789a74/data/train-0000$i-of-00007.parquet
done
B=$HF/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/data
curl -sL -o $D/mtbench/human-00000-of-00001-25f4910818759289.parquet $B/human-00000-of-00001-25f4910818759289.parquet
curl -sL -o $D/mtbench/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet $B/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet
curl -sL -o $D/nba/nbaallelo.csv https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv
J=$HF/potsawee/chatbot-arena-llm-judges/resolve/638a7e3be3078e55d2eb0b789d34749747822c49
curl -sL -o $D/judges/train.single-turn.json $J/train.single-turn.json
for m in Athene-70B Mistral-7B-Instruct-v0.2 Meta-Llama-3-8B-Instruct; do
  curl -sL -o $D/judges/llm-judges-prob-avg/$m.jsonl $J/llm-judges-prob-avg/$m.jsonl
done
cd $D
sha256sum -c - <<'SUMS'
0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2  arena55k/train.csv
4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769  mtbench/human-00000-of-00001-25f4910818759289.parquet
d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc  nba/nbaallelo.csv
SUMS
# checksums observed when we downloaded the files (not given in the task description):
#  57068327ffb5f8fddb15fedbbfe40b26fe862da2326331e5cf64a42320a00e71  mtbench/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet
#  6ed8793f61931637b65c1f348e8cb3a050996eef2a8c5c37c0b42fcfe465c8f3  judges/train.single-turn.json
#  dd6b1925ef6f2f5f5fa24799c57070ed23e587cef050784107b7251b69394b91  judges/llm-judges-prob-avg/Athene-70B.jsonl
#  3cd14efa0670141e587091032e4a51fefa7aaaf0b95ac84fca7b7aa234b70891  judges/llm-judges-prob-avg/Meta-Llama-3-8B-Instruct.jsonl
#  36e544b15e8741e7d5951fd4fb4f1c333e7626534a654c471aaf761e159ded25  judges/llm-judges-prob-avg/Mistral-7B-Instruct-v0.2.jsonl
# Arena-140k parquet checksums observed at download (not given in the task description):
#  7b871a964dc9b238fe0d59f817dbe1a7a56934e23ec4d989f86e6891e5a891cf  train-00000-of-00007.parquet
#  0cd29a6e3261159f41a69b28cd7f08c0bbbc1ef08ba18438d386a1b0c144af8a  train-00001-of-00007.parquet
#  c633264fe8f0fa26cc9aa49961a75dc428791f70c7a476cbed766963b88bee24  train-00002-of-00007.parquet
#  5bcf04c9f4488006a4a7ee944d886ee123e118b7f7d2db04b4ff6dbd8125e6b0  train-00003-of-00007.parquet
#  2c50b4b3f6a5c02d660f5a70d5006332ddc00f5eb21f8e4d92bde3856647969b  train-00004-of-00007.parquet
#  de59f74dce7477beaec55936b31a88537b93c5cbb4b483cfc6879a6862ce5e3b  train-00005-of-00007.parquet
#  1a32a1c6934ebcaa3019643a08fb57563ee0a9be282d3222def3c572a49e9f4c  train-00006-of-00007.parquet
