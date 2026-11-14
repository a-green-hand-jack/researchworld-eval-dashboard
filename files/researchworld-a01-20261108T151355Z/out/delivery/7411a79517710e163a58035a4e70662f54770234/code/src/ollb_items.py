"""Item counts per OLLB task (from one pinned lm-eval results JSON, field 'n-samples') and per-task normalisation floors
(solved from the paired Raw/normalised columns). Output: data/processed/ollb_noise.json.
Usage: python3 src/ollb_items.py OUT_JSON  (needs network for the single results file)
"""
import json, sys, urllib.request, hashlib
import pandas as pd, numpy as np
URL = ("https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/aa81ecc38fdc5708254b833923368970efdf5ef5/"
       "0-hero/Matter-0.2-7B-DPO/results_2024-08-07T13-21-02.903091.json")
raw = urllib.request.urlopen(URL, timeout=60).read()
ns = json.loads(raw)["n-samples"]
pref = {"IFEval": "leaderboard_ifeval", "BBH": "leaderboard_bbh_", "MATH Lvl 5": "leaderboard_math_", "GPQA": "leaderboard_gpqa_",
        "MUSR": "leaderboard_musr_", "MMLU-PRO": "leaderboard_mmlu_pro"}
items = {t: int(sum(v["effective"] for k, v in ns.items() if k.startswith(p))) for t, p in pref.items()}
d = pd.read_csv("data/processed/ollb6.csv")
floor = {}
for t in pref:
    m = (d[t] > 1) & (d[t] < 99)
    L = (d[t + " Raw"][m] - d[t][m] / 100) / (1 - d[t][m] / 100)
    floor[t] = float(np.median(L)); print(t, "floor std across models", round(float(L.std()), 5))   # BBH: per-subtask floors, so only approximately constant
json.dump({"source_sha256": hashlib.sha256(raw).hexdigest(), "n_items": items, "floor": floor}, open(sys.argv[1], "w"), indent=1)
print(items, floor)
