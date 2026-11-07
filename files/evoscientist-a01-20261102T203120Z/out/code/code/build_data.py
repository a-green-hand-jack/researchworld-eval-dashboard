"""Build processed score matrices from the raw public data.

Inputs (see README for how to fetch):
  data/contents.parquet            Open LLM Leaderboard `contents` (sha 9c09a7c...)
  data/oll_results/                git clone of Open LLM Leaderboard `results` (sha aa81ecc...)
  data/helm_v1.13.0/               HELM-MMLU release v1.13.0 summaries
Outputs (data/processed/):
  oll6.csv      models x 6 official tasks (normalised 0-100 scores) + metadata
  oll6_n.json   test-set sizes per task (for binomial noise model)
  bbh24.csv     models x 24 BBH sub-tasks (raw acc_norm in [0,1]); *_se columns hold reported stderr
  helm57.csv    models x 57 MMLU subjects (accuracy in [0,1]); n_eval json alongside
"""
import glob, json, os, re, hashlib
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
D = os.path.join(ROOT, "data")
OUT = os.path.join(D, "processed")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- OLL contents (6 official tasks)
c = pd.read_parquet(os.path.join(D, "contents.parquet"))
TASKS6 = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]
c = c.sort_values("Submission Date").drop_duplicates("fullname", keep="last")
meta_cols = ["fullname", "Type", "#Params (B)", "Flagged", "Merged", "MoE", "Base Model", "Submission Date",
             "Official Providers", "Average ⬆️"]
oll6 = c[meta_cols + TASKS6 + [t + " Raw" for t in TASKS6]].copy()
assert oll6[TASKS6].notna().all().all()
# sanity: official average == mean of the 6 normalised scores
dev = np.abs(oll6[TASKS6].mean(axis=1) - oll6["Average ⬆️"]).max()
print("max |mean(6 normalised) - official Average| =", dev)
oll6.to_csv(os.path.join(OUT, "oll6.csv"), index=False)
# test-set sizes (IFEval 541 prompts, BBH 5761, MATH-L5 1324, GPQA 1192, MuSR 756, MMLU-Pro 12032)
json.dump({"IFEval": 541, "BBH": 5761, "MATH Lvl 5": 1324, "GPQA": 1192, "MUSR": 756, "MMLU-PRO": 12032},
          open(os.path.join(OUT, "oll6_n.json"), "w"))
print("oll6", oll6.shape, "flagged", int(oll6.Flagged.sum()))

# ---------------------------------------------------------------- BBH-24 from per-run result JSONs
BBH = None
rows = {}
for f in glob.glob(os.path.join(D, "oll_results", "*", "*", "results_*.json")):
    parts = f.split(os.sep)
    name = parts[-3] + "/" + parts[-2]
    ts = os.path.basename(f)[len("results_"):-len(".json")]
    if name in rows and rows[name][0] >= ts:
        continue
    rows[name] = (ts, f)
recs = {}
nsamp = {}
for name, (ts, f) in rows.items():
    try:
        d = json.load(open(f))
    except Exception:
        continue
    r = d["results"]
    keys = sorted(k for k in r if k.startswith("leaderboard_bbh_"))
    if len(keys) != 24:
        continue
    rec = {}
    ok = True
    for k in keys:
        v = r[k].get("acc_norm,none"); se = r[k].get("acc_norm_stderr,none")
        if v is None or isinstance(se, str) or se is None:
            ok = False; break
        rec[k[len("leaderboard_bbh_"):]] = v
        rec[k[len("leaderboard_bbh_"):] + "_se"] = se
        nsamp[k[len("leaderboard_bbh_"):]] = d["n-samples"][k]["effective"]
    if ok:
        rec["run_ts"] = ts
        recs[name] = rec
bbh = pd.DataFrame.from_dict(recs, orient="index").rename_axis("fullname").reset_index()
tasks = [k for k in bbh.columns if k not in ("fullname", "run_ts") and not k.endswith("_se")]
# restrict to models in the (deduplicated) contents table
bbh = bbh.merge(oll6[["fullname", "Type", "#Params (B)", "Flagged", "Merged", "Base Model", "Official Providers"]],
                on="fullname", how="inner")
bbh.to_csv(os.path.join(OUT, "bbh24.csv"), index=False)
json.dump(nsamp, open(os.path.join(OUT, "bbh24_n.json"), "w"))
print("bbh24", bbh.shape, "n tasks", len(tasks), "of", len(recs), "models with full BBH")

# ---------------------------------------------------------------- HELM MMLU
gdir = os.path.join(D, "helm_v1.13.0", "groups", "json")
cols, neval = {}, {}
for f in sorted(glob.glob(os.path.join(gdir, "mmlu_*_subject:*.json"))):
    subj = re.search(r"subject:(.*)\.json$", f).group(1)
    d = json.load(open(f))
    hdr = [h["value"] for h in d["header"]]
    iem, ine = hdr.index("EM"), hdr.index("# eval")
    s = {}
    for row in d["rows"]:
        m = row[0]["value"]
        v = row[iem].get("value")
        if v is not None:
            s[m] = v
            neval[subj] = row[ine].get("value")
    cols[subj] = s
helm = pd.DataFrame(cols)
print("helm raw", helm.shape, "missing cells", int(helm.isna().sum().sum()))
helm.rename_axis("model").reset_index().to_csv(os.path.join(OUT, "helm57_all.csv"), index=False)
full = helm.dropna(axis=0, how="any")
print("helm complete models", full.shape)
full.rename_axis("model").reset_index().to_csv(os.path.join(OUT, "helm57.csv"), index=False)
json.dump(neval, open(os.path.join(OUT, "helm57_n.json"), "w"))

# ---------------------------------------------------------------- checksums
with open(os.path.join(OUT, "SHA256SUMS"), "w") as fh:
    for p in sorted(glob.glob(os.path.join(OUT, "*"))):
        if os.path.basename(p) != "SHA256SUMS":
            fh.write(hashlib.sha256(open(p, "rb").read()).hexdigest() + "  " + os.path.basename(p) + "\n")
fh = hashlib.sha256(open(os.path.join(D, "contents.parquet"), "rb").read()).hexdigest()
print("contents.parquet sha256", fh)
