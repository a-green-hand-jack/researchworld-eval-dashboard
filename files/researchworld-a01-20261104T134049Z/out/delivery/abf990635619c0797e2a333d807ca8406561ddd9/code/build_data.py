"""Build model x task score matrices from the raw downloads.
Usage: python3 code/build_data.py OLLB_PARQUET HELM_DIR OUTDIR
Outputs (OUTDIR): ollb6.csv (all models, normalised + raw task scores + metadata), helm_mmlu57.csv, manifest.json
"""
import hashlib, json, sys, pathlib
import pandas as pd, numpy as np

ollb_pq, helm_dir, out = map(pathlib.Path, sys.argv[1:4]); out.mkdir(parents=True, exist_ok=True)
TASKS = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

d = pd.read_parquet(ollb_pq)
n0 = len(d)
meta = ["fullname", "Precision", "Type", "Architecture", "Hub License", "#Params (B)", "Flagged", "Merged", "MoE",
        "Official Providers", "Base Model", "Generation", "Submission Date", "Average ⬆️"]
d = d[meta + TASKS + [t + " Raw" for t in TASKS]].copy()
d = d.sort_values("Average ⬆️", ascending=False, kind="stable")
n_dup = int(d.fullname.duplicated().sum())
d = d.drop_duplicates("fullname", keep="first")            # keep best-scoring precision/variant per model name
d.columns = [c.replace(" ⬆️", "") for c in d.columns]
d = d.reset_index(drop=True)
d.to_csv(out / "ollb6.csv", index=False)

# HELM MMLU v1.13.0: per-subject tables mmlu_mmlu_subject:<subject>.json ; column 'EM' of each table
rows = {}
for f in sorted((helm_dir / "groups" / "json").glob("mmlu_mmlu_subject:*.json")):
    subj = f.name[len("mmlu_mmlu_subject:"):-5]
    t = json.load(open(f)); hdr = [h["value"] for h in t["header"]]
    iem, ine = hdr.index("EM"), hdr.index("# eval")
    for r in t["rows"]:
        m = r[0]["value"]; v = r[iem].get("value"); ne = r[ine].get("value")
        rows.setdefault(m, {})[subj] = (v, ne)
subjects = sorted({s for m in rows.values() for s in m})
sc = pd.DataFrame({s: {m: rows[m].get(s, (np.nan, np.nan))[0] for m in rows} for s in subjects}) * 100
ne = pd.DataFrame({s: {m: rows[m].get(s, (np.nan, np.nan))[1] for m in rows} for s in subjects})
sc.index.name = "model"
full = sc.dropna()
sc.to_csv(out / "helm_mmlu_all.csv"); full.to_csv(out / "helm_mmlu57.csv")
ne.iloc[0].to_csv(out / "helm_mmlu_neval.csv", header=["n_eval"])
man = {"ollb_parquet_sha256": sha(ollb_pq), "ollb_rows_raw": n0, "ollb_rows_duplicate_fullname_dropped": n_dup,
       "ollb_rows_used": len(d), "helm_release": "v1.13.0", "helm_manifest_sha256": sha(helm_dir / "MANIFEST.sha256.json"),
       "helm_models_total": len(sc), "helm_models_complete": len(full), "helm_subjects": len(subjects)}
json.dump(man, open(out / "manifest.json", "w"), indent=1)
print(man)
