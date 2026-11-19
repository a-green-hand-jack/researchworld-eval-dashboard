"""Download the two Qwen2.5 instruct models (weights + tokenizer, no gguf/onnx) into data/models/."""
from huggingface_hub import snapshot_download
for m in ["Qwen/Qwen2.5-0.5B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"]:
    print(snapshot_download(m, local_dir="data/models/" + m.split("/")[1], allow_patterns=["*.json", "*.safetensors", "*.txt", "merges*"]))
