"""Download MMLU-Pro at the pinned revision (parquet) into data/."""
from huggingface_hub import snapshot_download
REV = "b189ec765aa7ed75c8acfea42df31fdae71f97be"
p = snapshot_download("TIGER-Lab/MMLU-Pro", repo_type="dataset", revision=REV, local_dir="data/mmlu_pro")
print(p)
