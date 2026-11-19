"""Download MMLU-Pro (pinned revision) and the Qwen2.5 models used in the paper into /work/{data,models}."""
from huggingface_hub import snapshot_download
snapshot_download("TIGER-Lab/MMLU-Pro", repo_type="dataset", revision="b189ec765aa7ed75c8acfea42df31fdae71f97be", local_dir="/work/data/mmlu-pro")
REV = {"Qwen/Qwen2.5-1.5B-Instruct": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
       "Qwen/Qwen2.5-0.5B-Instruct": "7ae557604adf67be50417f59c2c2f167def9a775",
       "HuggingFaceTB/SmolLM2-1.7B-Instruct": "31b70e2e869a7173562077fd711b654946d38674"}   # revisions actually used
for m, rev in REV.items():
    snapshot_download(m, revision=rev, local_dir="/work/models/" + m.split('/')[1], allow_patterns=["*.json", "*.safetensors", "*.txt"])
