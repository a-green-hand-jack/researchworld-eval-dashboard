"""Turn results/core/*.npz into instance-level metric table results/core_metrics.csv."""
import os, sys, glob
import numpy as np, pandas as pd
from data import RESULTS
from shapsim import pair_metrics, nogueira, _order

suffix = "_quick" if "--quick" in sys.argv else ""
rows = []
rng = np.random.default_rng(7)
for f in sorted(glob.glob(os.path.join(RESULTS, "core", f"*_*{suffix}.npz"))):
    base = os.path.basename(f)[:-4]
    if suffix == "" and base.endswith("_quick"):
        continue
    if base in ("cpu_time", "model_scores"):
        continue
    ds, kind = base.replace("_quick", "").split("_")
    Z = np.load(f)
    d, R = int(Z["d"]), int(Z["R"])
    N = len(Z["inst"])
    iu = np.triu_indices(R, 1)
    sel = rng.choice(len(iu[0]), min(300, len(iu[0])), replace=False)
    I, J = iu[0][sel], iu[1][sel]
    for scale in ("prob", "logit"):
        if f"ref_{scale}" not in Z.files:
            continue
        for key in Z.files:
            if not key.startswith(f"phi_{scale}_"):
                continue
            _, _, est, mult = key.split("_")
            mult = int(mult)
            nev = int(Z[f"nev_{scale}_{est}_{mult}"])
            PH = Z[key]  # (N,R,d)
            for n in range(N):
                P = PH[n]
                ref = Z[f"ref_{scale}"][n]
                meta = Z[f"meta_{scale}"][n]
                rr = pair_metrics(P[I], P[J])
                row = {k: float(np.nanmean(v)) for k, v in rr.items()}
                rf = pair_metrics(P, np.broadcast_to(ref, P.shape))
                for k, v in rf.items():
                    row["ref_" + k] = float(np.nanmean(v))
                row["ref_rel_err"] = float(np.mean(np.linalg.norm(P - ref, axis=1)) / (np.linalg.norm(ref) + 1e-12))
                top3 = np.zeros((R, d), bool)
                o = _order(P)[:, :3]
                np.put_along_axis(top3, o, True, axis=1)
                row["nogueira3"] = float(nogueira(top3))
                sd = P.std(0, ddof=1)
                ra = np.sort(np.abs(ref))[::-1]
                row.update(dataset=ds, model=kind, scale=scale, est=est, mult=mult, budget=mult * d, nev=nev, d=d, R=R,
                           inst=n, px=float(Z["y"][n] * 0 + meta[2]) if scale == "prob" else np.nan,
                           nonadd=float(meta[0]), v_null=float(meta[1]), v_x=float(meta[2]),
                           ref_norm=float(np.linalg.norm(ref)),
                           noise_ratio=float(np.linalg.norm(sd) / (np.linalg.norm(ref) + 1e-12)),
                           gap1=float((ra[0] - ra[1]) / (np.linalg.norm(ref) + 1e-12)),
                           gap3=float((ra[2] - ra[3]) / (np.linalg.norm(ref) + 1e-12)),
                           exact=bool(est == "kernel" and nev >= 2 ** d - 2 and d <= 12))
                rows.append(row)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(RESULTS, f"core_metrics{suffix}.csv"), index=False)
print(df.shape)
print(df.groupby(["dataset", "scale", "est", "mult"])[["top1", "jac3", "rbo", "tau", "rel_l2"]].median().round(3).head(60))
