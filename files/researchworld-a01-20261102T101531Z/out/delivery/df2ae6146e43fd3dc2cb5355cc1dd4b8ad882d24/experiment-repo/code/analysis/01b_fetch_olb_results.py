"""Bounded fetch of Open LLM Leaderboard `results` (pinned sha) for the
sub-task level.  Selection rule fixed before looking at any sub-task value:
population = `main` population of the headline analysis (unflagged, one row
per fullname, best Average) that has a results directory; take the top 300 by
Average plus 400 random others (numpy seed 20261102); for each model the
lexicographically last (= latest dated) results_*.json.
Writes data/raw/olb_results/<org>__<name>.json, data/processed/olb_subtask.csv
(raw accuracies in points, 39 sub-tasks) and data/processed/olb_results_manifest.json."""
import json, hashlib, os, sys, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from common import *
SHA = "aa81ecc38fdc5708254b833923368970efdf5ef5"
RAWD = f"{ROOT}/data/raw/olb_results"; os.makedirs(RAWD, exist_ok=True)
tree = json.load(urllib.request.urlopen(f"https://huggingface.co/api/datasets/open-llm-leaderboard/results/revision/{SHA}?blobs=true"))
by = {}
for s in tree["siblings"]:
    f = s["rfilename"]
    if f.count("/") >= 2 and f.endswith(".json"):
        by.setdefault("/".join(f.split("/")[:2]), []).append((f, s.get("size")))
o, S = load_olb("main")
o = o[o["fullname"].isin(by)].sort_values("avg", ascending=False).reset_index(drop=True)
rng = np.random.default_rng(20261102)
top = o.iloc[:300]; rest = o.iloc[300:]
sel = pd.concat([top, rest.iloc[rng.choice(len(rest), 400, replace=False)]])
print("selected", len(sel), "of", len(o), flush=True)
def get(name):
    f = sorted(by[name])[-1][0]
    out = f"{RAWD}/{name.replace('/', '__')}.json"
    if not os.path.exists(out):
        url = f"https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/{SHA}/{urllib.parse.quote(f)}"
        for _ in range(4):
            try:
                open(out, "wb").write(urllib.request.urlopen(url, timeout=60).read()); break
            except Exception as e: err = e
        else: return name, f, None
    return name, f, hashlib.sha256(open(out, "rb").read()).hexdigest()
with ThreadPoolExecutor(8) as ex: res = list(ex.map(get, sel["fullname"]))
man = {n: {"file": f, "sha256": h} for n, f, h in res}
json.dump({"dataset_sha": SHA, "files": man}, open(f"{ROOT}/data/processed/olb_results_manifest.json", "w"), indent=1)
KEYS = {}
rows = []
for n, f, h in res:
    if h is None: continue
    r = json.load(open(f"{RAWD}/{n.replace('/', '__')}.json"))["results"]
    row = {"fullname": n}
    for k, v in r.items():
        if k.startswith("leaderboard_bbh_"): row[k] = v["acc_norm,none"]
        elif k.startswith("leaderboard_gpqa_") or k.startswith("leaderboard_musr_"): row[k] = v["acc_norm,none"]
        elif k.startswith("leaderboard_math_") and k != "leaderboard_math_hard": row[k] = v["exact_match,none"]
        elif k == "leaderboard_mmlu_pro": row[k] = v["acc,none"]
        elif k == "leaderboard_ifeval": row[k] = (v["prompt_level_strict_acc,none"] + v["inst_level_strict_acc,none"]) / 2
    rows.append(row)
df = pd.DataFrame(rows).set_index("fullname")
df = 100 * df.dropna(axis=0, how="any")   # a model lacking any sub-task (1 of 700) is dropped
print(df.shape)
df.to_csv(f"{ROOT}/data/processed/olb_subtask.csv")
