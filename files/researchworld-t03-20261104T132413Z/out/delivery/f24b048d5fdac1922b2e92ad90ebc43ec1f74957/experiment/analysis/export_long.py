"""Stage 0 (export): raw npz -> long-format parquet for plotting.

usage: python3 analysis/export_long.py [raw_dir] [out_dir]
runs.parquet       one row per (dataset, model, explainer, budget_idx, inst, run): nominal budget, rows evaluated,
                   seed passed to the explainer, attribution vector `phi` (list of d floats)
reference.parquet  one row per (dataset, model, inst): model P(y=1), reference vector, its SE, how it was computed
comparison.parquet one row per (dataset, model, comparison, inst, member): retrain / background attribution vectors
cells.csv is written by build_tables.py (test metrics).
"""
import glob, json, os, sys
import numpy as np, pandas as pd

raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results", "raw")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "results", "long")
os.makedirs(out, exist_ok=True)
runs, refs, comps = [], [], []
cells = sorted({os.path.basename(p).rsplit("__", 1)[0] for p in glob.glob(f"{raw}/*__ref.npz")})
for cell in cells:
    ds, model = cell.split("__")
    z = np.load(f"{raw}/{cell}__ref.npz"); meta = json.loads(str(z["meta"]))
    exact = bool((z["ref_se"] == 0).all())
    for i in range(len(z["p"])):
        refs.append(dict(dataset=ds, model=model, inst=i, test_row=int(z["sel"][i]), p=float(z["p"][i]), ref=z["ref"][i].tolist(),
                         ref_se=z["ref_se"][i].tolist(), ref_method="enumeration" if exact else "mean of 10 Kernel SHAP runs, 20000 coalitions",
                         model_seed=meta["seed"], background_size=meta["B"], test_auc=meta["test_auc"]))
    for ex in ("kernel", "perm", "kernell1"):
        f = f"{raw}/{cell}__{ex}.npz"
        if not os.path.exists(f):
            continue
        zz = np.load(f); phi, rows, bud = zz["phi"], zz["rows"], zz["budgets"]
        N, nb, R, d = phi.shape
        for i in range(N):
            for b in range(nb):
                for r in range(R):
                    runs.append(dict(dataset=ds, model=model, explainer={"kernell1": "kernel_l1default"}.get(ex, ex), budget_idx=b,
                                     budget_nominal=int(bud[b]), rows_evaluated=int(rows[i, b, r]), inst=i, run=r,
                                     seed=10_000 * (i + 1) + 100 * b + r, phi=phi[i, b, r].tolist()))
    for name, key in (("retrain", None), ("bg", None)):
        f = f"{raw}/{cell}__{name}.npz"
        if not os.path.exists(f):
            continue
        zz = np.load(f)
        for kk in zz.files:
            if not kk.startswith("phi"):
                continue
            arr = zz[kk]
            comp = name if name == "retrain" else "background_" + kk[4:]
            for m in range(arr.shape[0]):
                for i in range(arr.shape[1]):
                    comps.append(dict(dataset=ds, model=model, comparison=comp, inst=i, member=m, phi=arr[m, i].tolist()))
pd.DataFrame(runs).to_parquet(f"{out}/runs.parquet", index=False)
pd.DataFrame(refs).to_parquet(f"{out}/reference.parquet", index=False)
pd.DataFrame(comps).to_parquet(f"{out}/comparison.parquet", index=False)
print({k: len(v) for k, v in dict(runs=runs, refs=refs, comps=comps).items()})
