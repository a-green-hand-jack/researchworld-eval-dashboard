"""HELM MMLU v1.13.0 groups/mmlu_subjects.json 'Accuracy' table -> wide parquet (79 models x 57 subjects, EM).
usage: python3 -I build_helm_mmlu.py RAWDIR OUT.parquet"""
import json, sys, re
import pandas as pd
raw, out = sys.argv[1:3]
tabs = json.load(open(f"{raw}/groups_mmlu_subjects.json"))
acc = [t for t in tabs if t["title"] == "Accuracy"][0]
schema = json.load(open(f"{raw}/schema.json"))
meta = {m["display_name"]: m for m in schema["models"]}
hdr = [h["value"] for h in acc["header"]]
rows = []
for r in acc["rows"]:
    d = {"model": r[0]["value"]}
    names = set()
    for c in r[1:]:
        for rs in c.get("run_spec_names", []):
            m = re.search(r"model=([^,]+)", rs)
            if m: names.add(m.group(1))
    d["model_run_name"] = ";".join(sorted(names))
    for h, c in zip(hdr[1:], r[1:]):
        assert h.endswith(" - EM"), h
        key = "mmlu_all_subjects_em" if h.startswith("MMLU All Subjects") else "mmlu_" + re.sub(r"[^a-z0-9]+", "_", h[:-5].lower()).strip("_")
        d[key] = c.get("value")
    m = meta.get(d["model"], {})
    for k in ["creator_organization", "access", "release_date", "num_parameters"]: d[k] = m.get(k)
    rows.append(d)
df = pd.DataFrame(rows)
df["release_date"] = pd.to_datetime(df["release_date"])
sub = [c for c in df if c.startswith("mmlu_") and c != "mmlu_all_subjects_em"]
print(df.shape, "subjects", len(sub), "missing frac", df[sub].isna().mean().mean(), "dup", df.model.duplicated().sum(),
      "no meta", df.creator_organization.isna().sum(), "no run name", (df.model_run_name == "").sum())
df.to_parquet(out, index=False)
