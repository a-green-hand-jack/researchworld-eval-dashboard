"""Build tidy score matrices from the raw downloads.

Outputs (data/processed/):
  helm_mmlu_v1.13.0.csv     model x 57 subjects, accuracy in points (0-100)
  helm_mmlu_neval.csv       number of eval instances per subject (same shape)
  olb_contents.csv          Open LLM Leaderboard (contents@9c09a7c): metadata +
                            6 normalised task scores + 6 raw scores
  manifest.json             SHA-256 of every raw file used
"""
import glob, hashlib, json, os, sys
import numpy as np, pandas as pd

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../code
ROOT = os.path.dirname(CODE)
RAW, OUT = f"{ROOT}/data/raw", f"{ROOT}/data/processed"
os.makedirs(OUT, exist_ok=True)

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

manifest = {}
# ---- HELM MMLU
acc, neval = {}, {}
files = sorted(glob.glob(f"{RAW}/helm/groups/json/mmlu_mmlu_subject:*.json"))
assert len(files) == 57, len(files)
for f in files:
    d = json.load(open(f))
    subj = d["name"].split(":")[1]
    hdr = [h["value"] for h in d["header"]]
    ie, ine = hdr.index("EM"), hdr.index("# eval")
    for r in d["rows"]:
        name = r[0]["value"]
        acc.setdefault(name, {})[subj] = None if r[ie].get("value") is None else 100 * r[ie]["value"]
        neval.setdefault(name, {})[subj] = r[ine].get("value")
    manifest[os.path.relpath(f, ROOT)] = sha(f)
A = pd.DataFrame(acc).T.sort_index(axis=1)
N = pd.DataFrame(neval).T.sort_index(axis=1)
print("HELM raw:", A.shape, "missing cells:", int(A.isna().sum().sum()))
full = A.dropna()
print("HELM complete models:", full.shape[0], "dropped:", list(A.index.difference(full.index)))
full.to_csv(f"{OUT}/helm_mmlu_v1.13.0.csv"); N.loc[full.index].to_csv(f"{OUT}/helm_mmlu_neval.csv")

# ---- Open LLM Leaderboard contents
p = f"{RAW}/olb_contents/train-00000-of-00001.parquet"
d = pd.read_parquet(p); manifest[os.path.relpath(p, ROOT)] = sha(p)
d.to_csv(f"{OUT}/olb_contents.csv", index=False)
print("OLB:", d.shape)
json.dump(manifest, open(f"{OUT}/manifest.json", "w"), indent=1, sort_keys=True)
