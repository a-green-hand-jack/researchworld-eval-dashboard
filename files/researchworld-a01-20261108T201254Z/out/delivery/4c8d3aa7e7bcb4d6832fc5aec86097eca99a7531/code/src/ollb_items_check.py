"""Are the OLLB item counts the same across models? (external-review request #6.3b)
Usage: python3 src/ollb_items_check.py OUT_CSV [N_MODELS=60]      (needs network: HF API + one results JSON per sampled model)
Samples N model directories (the latest results JSON of each that contains all six tasks) of the pinned `results` snapshot at random (seed 0; org/model directories among all), downloads their results JSONs, latest first, and sums `n-samples.<task>.effective` per OLLB task exactly as src/ollb_items.py does. Output: one row per model.
"""
import json, sys, urllib.request, urllib.parse, random
import numpy as np, pandas as pd
REV = "aa81ecc38fdc5708254b833923368970efdf5ef5"; N = int(sys.argv[2]) if len(sys.argv) > 2 else 60
API = f"https://huggingface.co/api/datasets/open-llm-leaderboard/results/tree/{REV}/"
RAW = f"https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/{REV}/"
PREF = {"IFEval": "leaderboard_ifeval", "BBH": "leaderboard_bbh_", "MATH Lvl 5": "leaderboard_math_", "GPQA": "leaderboard_gpqa_",
        "MUSR": "leaderboard_musr_", "MMLU-PRO": "leaderboard_mmlu_pro"}
get = lambda u: urllib.request.urlopen(u, timeout=60).read()

def tree(path=""):
    out, url = [], API + urllib.parse.quote(path) + ("?" if not path else "?") + "limit=1000"
    while url:
        resp = urllib.request.urlopen(url, timeout=60); out += json.loads(resp.read())
        nxt = [l for l in (resp.headers.get("Link") or "").split(",") if 'rel="next"' in l]
        url = nxt[0].split(";")[0].strip(" <>") if nxt else None
    return out
orgs = [e["path"] for e in tree() if e["type"] == "directory"]
rng = random.Random(0); rng.shuffle(orgs); rows = []
for org in orgs:
    if len(rows) >= N: break
    try:
        ents = tree(org); models = [e["path"] for e in ents if e["type"] == "directory"]
        files = [e["path"] for e in ents if e["type"] == "file" and e["path"].endswith(".json")]
        if models: m = rng.choice(models); files = [e["path"] for e in tree(m) if e["type"] == "file" and e["path"].endswith(".json")]
        if not files: continue
        for f in sorted(files, reverse=True):      # latest file first; a file that lacks one of the six tasks is a partial run and is skipped (and counted)
            ns = json.loads(get(RAW + urllib.parse.quote(f)))["n-samples"]
            items = {t: int(sum(v["effective"] for k, v in ns.items() if k.startswith(p))) for t, p in PREF.items()}
            if all(v > 0 for v in items.values()): break
        else: continue
    except Exception as ex:
        print("skip", org, ex, flush=True); continue
    rows.append(dict(file=f, n_files_listed=len(files), n_partial_files_skipped=sorted(files, reverse=True).index(f), **items)); print(len(rows), f, items, flush=True)
D = pd.DataFrame(rows); D.to_csv(sys.argv[1], index=False)
print("distinct item-count vectors across", len(D), "models:", len(D[list(PREF)].drop_duplicates()))
print(D[list(PREF)].describe().loc[["min", "max"]])
