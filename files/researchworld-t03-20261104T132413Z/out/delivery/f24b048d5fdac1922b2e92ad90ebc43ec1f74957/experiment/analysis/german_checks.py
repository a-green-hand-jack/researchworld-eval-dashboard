"""Checks specific to the d>16-unenumerable-reference cell (German, d=20) and to the shap default l1_reg.

usage: python3 analysis/german_checks.py [raw_dir] [out_dir]
Writes
  <out>/ref_check.csv   per (model, instance in the first 3): relative L2 distance of the converged-Kernel reference
                        (mean of K_ref runs at m_ref coalitions) to the 2^d enumeration, next to its stored SE and to the
                        median error of one Kernel run at the largest budget (the residual reference error must be small
                        relative to that noise for the reference to be usable)
  <out>/l1_default.csv  Kernel SHAP with l1_reg=False (main grid) vs the library default l1_reg="num_features(10)":
                        per budget the median relative error, top-k match to the reference and the share of runs whose
                        top-k set changed (instance-cluster bootstrap CIs)
"""
import glob, json, os, sys
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import metrics as M

raw = sys.argv[1] if len(sys.argv) > 1 else "results/raw"
out = sys.argv[2] if len(sys.argv) > 2 else "results/tables"
rng = np.random.RandomState(12345)
rc, l1 = [], []
for f in sorted(glob.glob(f"{raw}/*__refcheck.npz")):
    cell = os.path.basename(f)[:-len("__refcheck.npz")]
    ds, model = cell.split("__")
    if not os.path.exists(f"{raw}/{cell}__ref.npz"):
        continue
    ex = np.load(f)["exact"]
    for fm in sorted(glob.glob(f"{raw}/{cell}__refcheckmore_*.npz"), key=lambda x: int(os.path.basename(x).split("_")[-2])):
        zm = np.load(fm)
        if int(zm["first"]) == len(ex):          # chunks of further instances, contiguous with the first three
            ex = np.concatenate([ex, zm["exact"]])
    z = np.load(f"{raw}/{cell}__ref.npz")
    ref, se = z["ref"], z["ref_se"]
    kz = np.load(f"{raw}/{cell}__kernel.npz") if os.path.exists(f"{raw}/{cell}__kernel.npz") else None
    for i in range(len(ex)):
        nx = np.linalg.norm(ex[i])
        row = dict(dataset=ds, model=model, inst=i, ref_vs_exact_rel=np.linalg.norm(ref[i] - ex[i]) / nx,
                   ref_se_rel=np.linalg.norm(se[i]) / nx,
                   top3_equal=bool((M.topk_ind(ref[i][None], 3) == M.topk_ind(ex[i][None], 3)).all()),
                   top5_equal=bool((M.topk_ind(ref[i][None], 5) == M.topk_ind(ex[i][None], 5)).all()))
        if kz is not None:
            phi = kz["phi"][i, -1]
            row["kernel_run_relerr_med_maxbudget_vs_exact"] = float(np.median(np.linalg.norm(phi - ex[i], axis=1) / nx))
            row["kernel_run_relerr_med_maxbudget_vs_ref"] = float(np.median(np.linalg.norm(phi - ref[i], axis=1) / np.linalg.norm(ref[i])))
        rc.append(row)
# default l1_reg stage: every cell that has it (it does not need the enumeration check)
for fl in sorted(glob.glob(f"{raw}/*__kernell1.npz")):
    cell = os.path.basename(fl)[:-len("__kernell1.npz")]
    ds, model = cell.split("__")
    if not (os.path.exists(f"{raw}/{cell}__ref.npz") and os.path.exists(f"{raw}/{cell}__kernel.npz")):
        continue
    ref = np.load(f"{raw}/{cell}__ref.npz")["ref"]
    kz = np.load(f"{raw}/{cell}__kernel.npz")
    zl = np.load(f"{raw}/{cell}__kernell1.npz")
    bud = kz["budgets"]
    for b in range(len(bud)):
        per = {"l1_false": [], "l1_default": []}
        for name, arr in (("l1_false", kz["phi"]), ("l1_default", zl["phi"])):
            for i in range(len(ref)):
                per[name].append(M.instance_metrics(arr[i, b], ref[i]))
        for name in per:
            df = pd.DataFrame(per[name])
            row = dict(dataset=ds, model=model, variant=name, budget=int(bud[b]), n_inst=len(df))
            for col in ("relerr_med", "match_ref_k1", "match_ref_k3", "match_ref_k5", "pair_match_k3", "rbo_ref"):
                m, lo, hi = M.boot_ci(df[col].values, rng, B=1000)
                row.update({col: m, col + "_lo": lo, col + "_hi": hi})
            l1.append(row)
        # share of (instance, run) pairs where the two variants (same seed) give different top-3 sets
        ch = [np.mean((M.topk_ind(kz["phi"][i, b], 3) != M.topk_ind(zl["phi"][i, b], 3)).any(1)) for i in range(len(ref))]
        m, lo, hi = M.boot_ci(np.array(ch), rng, B=1000)
        l1.append(dict(dataset=ds, model=model, variant="top3_changed_by_default_l1", budget=int(bud[b]), n_inst=len(ch),
                       match_ref_k3=m, match_ref_k3_lo=lo, match_ref_k3_hi=hi))
os.makedirs(out, exist_ok=True)
pd.DataFrame(rc).to_csv(f"{out}/ref_check.csv", index=False)
pd.DataFrame(l1).to_csv(f"{out}/l1_default.csv", index=False)
print(pd.DataFrame(rc).to_string())
