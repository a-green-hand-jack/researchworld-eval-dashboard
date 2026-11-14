"""Model metadata for the MTEB matrix (release date, adapted_from, parameters, family key).
usage: build_mteb_meta.py RESULTS_DIR MATRIX_CSV OUT_CSV
Uses model_meta.json of the revision directory with most task files (the one build_mteb.py used).
family = key of `adapted_from` if given, else key of the model name; key = lowercase leading letters of the name after the organisation
(first '-'/'_' token without trailing digits; 'org/token' if shorter than 3 letters: 'Alibaba-NLP__gte-Qwen2-7B-instruct' -> 'gte', 'intfloat__e5-large' -> 'intfloat/e'), a coarse proxy for a model family."""
import json, os, re, sys, pandas as pd
root, mat, out = sys.argv[1:4]
def key(name):
    n = name.replace("__", "/").lower(); org, _, base = n.rpartition("/")
    t = re.sub(r"[\d.]+$", "", re.split(r"[-_ ]", base)[0])
    return t if len(t) >= 3 else (org + "/" + t if org else t)
rows = {}
for model in pd.read_csv(mat, index_col=0, usecols=[0]).index:
    mdir = os.path.join(root, model); best = None
    for rev in os.listdir(mdir):
        p = os.path.join(mdir, rev)
        if not os.path.isdir(p): continue
        n = len([f for f in os.listdir(p) if f.endswith(".json") and f != "model_meta.json"])
        if best is None or n > best[0]: best = (n, p)
    meta = {}
    f = os.path.join(best[1], "model_meta.json") if best else None
    if f and os.path.exists(f):
        try: meta = json.load(open(f))
        except Exception: pass
    af = meta.get("adapted_from"); af = af[0] if isinstance(af, list) and af else af
    rows[model] = dict(release_date=meta.get("release_date"), adapted_from=af, n_parameters=meta.get("n_parameters"),
                       family=key(af if af else model.split("__")[-1]))
df = pd.DataFrame(rows).T; df.index.name = "model"; df.to_csv(out)
print(df.shape, "release_date present", df.release_date.notna().mean(), "adapted_from present", df.adapted_from.notna().mean(), "families", df.family.nunique())
