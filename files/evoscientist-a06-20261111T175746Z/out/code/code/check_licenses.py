import json, urllib.request
for r, t in (("Qwen/Qwen2.5-0.5B-Instruct", "model"), ("Qwen/Qwen2.5-1.5B-Instruct", "model"), ("TIGER-Lab/MMLU-Pro", "dataset")):
    d = json.load(urllib.request.urlopen(f"https://huggingface.co/api/{t}s/{r}", timeout=30))
    print(r, d.get("cardData", {}).get("license"), d.get("sha"))
