"""Build complete-case matrices with explicit, score-independent row selection."""
from pathlib import Path
import json
import re
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TASKS = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]

def save(name, frame, metadata):
    out = ROOT / "data/processed"
    out.mkdir(exist_ok=True, parents=True)
    frame.to_csv(out / f"{name}.csv", index_label="model", float_format="%.17g")
    (out / f"{name}_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

def main():
    tables, n_eval, raw_ids = {}, {}, {}
    for p in sorted((ROOT / "data/raw/helm").glob("*.json")):
        table = json.loads(p.read_text())
        names = [c["value"] for c in table["header"]]
        si, ni = names.index("EM"), names.index("# eval")
        subject = p.stem
        values, sizes = {}, set()
        for row in table["rows"]:
            specs = row[0].get("run_spec_names", [])
            # The summary identifies one evaluated model/protocol per row.
            assert len(specs) == 1, specs
            mid = re.search(r",model=([^,]+)", specs[0]).group(1)
            assert mid not in values
            values[mid] = row[si]["value"]
            raw_ids[mid] = row[0]["value"]
            if row[ni]["value"] is not None:
                sizes.add(row[ni]["value"])
        tables[subject] = values
        n_eval[subject] = sorted(sizes)
    frame = pd.DataFrame(tables).sort_index()
    n_raw = len(frame)
    missing = frame.isna().sum(axis=1)
    complete = frame.loc[missing == 0]
    assert complete.shape[1] == 57
    assert np.isfinite(complete.values).all()
    assert ((complete.values >= 0) & (complete.values <= 1)).all()
    meta = dict(raw_model_union=n_raw, complete_models=len(complete), tasks=57,
                dropped_missing=missing[missing > 0].to_dict(), display_names=raw_ids,
                n_eval_by_subject=n_eval,
                organization={m: m.split("_")[0] for m in complete.index})
    save("helm", complete, meta)
    # Subject sizes are invariant across models on this snapshot; check rather than assume.
    assert all(len(v) == 1 for v in n_eval.values())
    p = pd.read_parquet(ROOT / "data/raw/open_llm_contents.parquet")
    assert not p.eval_name.duplicated().any()
    clean = p.loc[~p.Flagged & np.isfinite(p[TASKS]).all(axis=1)].copy()
    priority = {"bfloat16": 0, "float16": 1, "float32": 2, "8bit": 3, "4bit": 4}
    clean["precision_priority"] = clean.Precision.map(priority).fillna(5)
    clean = clean.sort_values(["precision_priority", "eval_name"], kind="stable")
    unique = clean.drop_duplicates("fullname").sort_values("fullname")
    for name, source in [("oll", unique), ("oll_all_entries", clean.sort_values("eval_name"))]:
        key = "fullname" if name == "oll" else "eval_name"
        f = source.set_index(key)[TASKS] / 100
        assert ((f.values >= 0) & (f.values <= 1)).all()
        md = dict(raw_rows=len(p), unflagged_complete=len(clean), retained_rows=len(f),
                  unique_model_names=int(clean.fullname.nunique()), tasks=TASKS,
                  precision_priority=priority,
                  organization={str(r[key]): str(r['fullname']).split('/')[0] for _, r in source.iterrows()},
                  base_model={str(r[key]): str(r['Base Model']) for _, r in source.iterrows()},
                  eval_name={str(r[key]): str(r['eval_name']) for _, r in source.iterrows()})
        save(name, f, md)
    raw = unique.set_index("fullname")[[c + " Raw" for c in TASKS]]
    raw.columns = TASKS
    assert ((raw.values >= 0) & (raw.values <= 1)).all()
    save("oll_raw", raw, json.loads((ROOT / "data/processed/oll_metadata.json").read_text()))
    # The published Average must be the mean of displayed normalized metrics.
    average_error = np.max(np.abs(unique[TASKS].mean(axis=1) - unique["Average ⬆️"]))
    audit = dict(helm_shape=list(complete.shape), helm_incomplete=n_raw-len(complete),
                 oll_shape=list(raw.shape), oll_flagged=int(p.Flagged.sum()),
                 oll_duplicate_names_removed=len(clean)-len(unique),
                 published_average_max_abs_error=float(average_error),
                 oll_zero_cells=int((unique[TASKS] == 0).sum().sum()))
    (ROOT / "artifacts/data_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))

if __name__ == "__main__":
    main()
