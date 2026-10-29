set -x
cd data/raw
HF=https://huggingface.co/datasets
curl -sL -o arena55k_train.csv $HF/lmarena-ai/arena-human-preference-55k/resolve/18c298340948c0e7f7727399fd459cca6ce0ca6f/train.csv
curl -sL -o mtbench_human.parquet $HF/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/data/human-00000-of-00001-25f4910818759289.parquet
curl -sL -o mtbench_gpt4_pair.parquet $HF/lmsys/mt_bench_human_judgments/resolve/f7d2896d2cc5d80f8b55c2bbc722613555233c25/data/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet
curl -sL -o nbaallelo.csv https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv
mkdir -p llmjudges
curl -sL -o llmjudges/train.single-turn.json $HF/potsawee/chatbot-arena-llm-judges/resolve/638a7e3be3078e55d2eb0b789d34749747822c49/train.single-turn.json
for j in Athene-70B Hermes-3-Llama-3.1-70B Meta-Llama-3-70B-Instruct Meta-Llama-3-8B-Instruct Meta-Llama-3-8B Mistral-7B-Instruct-v0.1 Mistral-7B-Instruct-v0.2 Mistral-7B-OpenOrca Mixtral-8x7B-Instruct-v0.1 OpenHermes-2-Mistral-7B OpenHermes-2.5-Mistral-7B Qwen2-72B-Instruct StableBeluga-7B Starling-LM-7B-alpha dolphin-2.1-mistral-7b dolphin-2.5-mixtral-8x7b zephyr-7b-beta; do
 curl -sL -o llmjudges/$j.jsonl $HF/potsawee/chatbot-arena-llm-judges/resolve/638a7e3be3078e55d2eb0b789d34749747822c49/llm-judges/$j.jsonl
done
mkdir -p arena140k
for i in 0 1 2 3 4 5 6; do
 curl -sL -o arena140k/train-0000$i-of-00007.parquet $HF/lmarena-ai/arena-human-preference-140k/resolve/6322995ab34d7c2693e3f47dd13fa5caa0789a74/data/train-0000$i-of-00007.parquet
done
echo DONE
