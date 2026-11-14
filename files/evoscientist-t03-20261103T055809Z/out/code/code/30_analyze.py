"""Stage 3: metrics, noise floors and bootstrap CIs. Writes results/*.csv used by the figure/table scripts.

Pre-specified (before seeing results):
  primary metric   : top-3 Jaccard of |phi| rankings (J3); secondary: top-1 agreement, RBO(p=0.9,depth=min(d,10)),
                     Spearman of |phi|, relative L2 distance, sign agreement over the reference top-3.
  run-to-run       : all C(R,2) pairs of independent runs on the same (model, instance, background).
  error vs ref     : run vs exact interventional SHAP (where available).
  floors           : (i) background-draw floor: exact phi under another 100-row background vs exact phi (same model);
                     (ii) retrain floor: exact phi of retrained model (other seed) vs original;
                     (iii) between-instance floor: phi of instance i vs. a different random instance j;
                     (iv) global-importance floor: instance ref ranking vs. dataset-level mean|phi| ranking.
  decision rule    : a single run is 'adequate' for a cell if lower CI bound of mean pairwise J3 >= 0.8 (absolute rule)
                     and it is 'no worse than the background floor' if J3(run,run) >= J3(bg-alt, ref) (relative rule).
"""
import os, sys, itertools, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy.stats import rankdata
from common import *

K = 3
RNG = np.random.RandomState(2024)


def top(a, k):
    return set(np.argsort(-np.abs(a), kind="stable")[:k])


def rbo(a, b, p=0.9, depth=10):
    depth = min(depth, len(a))
    ra, rb = np.argsort(-np.abs(a), kind="stable")[:depth], np.argsort(-np.abs(b), kind="stable")[:depth]
    sa, sb, s = set(), set(), 0.0
    X = 0
    for i in range(1, depth + 1):
        sa.add(ra[i - 1]); sb.add(rb[i - 1]); X = len(sa & sb)
        s += (X / i) * p ** i
    return (X / depth) * p ** depth + (1 - p) / p * s


def metrics(a, b):
    """agreement of attribution vectors a,b (b may be reference). Returns dict."""
    ta, tb = top(a, K), top(b, K)
    ra, rb = rankdata(-np.abs(a)), rankdata(-np.abs(b))
    nb = np.linalg.norm(b)
    return dict(
        J3=len(ta & tb) / len(ta | tb),
        top1=float(np.argmax(np.abs(a)) == np.argmax(np.abs(b))),
        rbo=rbo(a, b),
        spear=np.corrcoef(ra, rb)[0, 1] if ra.std() > 0 and rb.std() > 0 else np.nan,
        relL2=np.linalg.norm(a - b) / (nb + 1e-12),
        sign3=float(np.mean([np.sign(a[j]) == np.sign(b[j]) for j in top(b, K)])),
    )


MK = ["J3", "top1", "rbo", "spear", "relL2", "sign3"]


def inst_mean(rows):
    return {k: np.nanmean([r[k] for r in rows]) for k in MK}


def boot_ci(v, n=2000):
    v = np.asarray(v, float); v = v[~np.isnan(v)]
    if len(v) == 0: return (np.nan, np.nan)
    idx = RNG.randint(0, len(v), (n, len(v)))
    m = v[idx].mean(1)
    return tuple(np.percentile(m, [2.5, 97.5]))


def main():
    cells, floors = [], []
    inst_rows = []
    for ds in DATASETS:
        for m in MODELS:
            fr = os.path.join(RES, f"runs_{ds}_{m}.npz")
            if not os.path.exists(fr): print("missing", ds, m); continue
            Z = np.load(fr)
            rf = os.path.join(RES, f"ref_{ds}_{m}.npz")
            R = np.load(rf) if os.path.exists(rf) else None
            ref = R["ref"] if R is not None else None
            # ---- floors (only where exact reference exists)
            if R is not None:
                n = ref.shape[0]
                for name, key in [("bg_floor", "bg_alt"), ("retrain_floor", "seed_alt")]:
                    if key in R.files:
                        per = [inst_mean([metrics(R[key][s, i], ref[i]) for s in range(R[key].shape[0])]) for i in range(n)]
                        for i, p in enumerate(per): floors.append(dict(dataset=ds, model=m, floor=name, inst=i, **p))
                per = []
                for i in range(n):
                    js = [j for j in range(n) if j != i]
                    per.append(inst_mean([metrics(ref[j], ref[i]) for j in js]))
                for i, p in enumerate(per): floors.append(dict(dataset=ds, model=m, floor="between_instance", inst=i, **p))
                g = np.abs(ref).mean(0)
                for i in range(n): floors.append(dict(dataset=ds, model=m, floor="global_importance", inst=i, **metrics(g, ref[i])))
            # ---- run-level metrics
            for ex in EXPLAINERS:
                for B in BUDGETS[ds]:
                    phi = Z[f"{ex}|{B}|phi"]  # (n_inst, R, d)
                    n, Rn, d = phi.shape
                    secs = Z[f"{ex}|{B}|secs"].mean(); rows = Z[f"{ex}|{B}|rows"].mean()
                    pair, vsref, avg = [], [], []
                    for i in range(n):
                        pr = [metrics(phi[i, a], phi[i, b]) for a, b in itertools.combinations(range(Rn), 2)]
                        pair.append(inst_mean(pr))
                        if ref is not None:
                            vsref.append(inst_mean([metrics(phi[i, r], ref[i]) for r in range(Rn)]))
                            # averaging m runs (m=5) vs ref
                            avg.append(metrics(phi[i, :5].mean(0), ref[i]))
                    for i in range(n):
                        row = dict(dataset=ds, model=m, explainer=ex, B=B, d=d, inst=i,
                                   exact_cap=int(B >= 2 ** d - 2), ref_std=float(phi[i].std(0).mean()))
                        row.update({f"rr_{k}": pair[i][k] for k in MK})
                        if ref is not None:
                            row.update({f"ref_{k}": vsref[i][k] for k in MK})
                            row.update({f"avg5_{k}": avg[i][k] for k in MK})
                            srt = np.sort(np.abs(ref[i]))[::-1]
                            row["gap34"] = (srt[K - 1] - srt[K]) / (srt[0] + 1e-12)
                        inst_rows.append(row)
                    print(ds, m, ex, B, "done", flush=True)
    I = pd.DataFrame(inst_rows); I.to_csv(os.path.join(RES, "instance_metrics.csv"), index=False)
    F = pd.DataFrame(floors); F.to_csv(os.path.join(RES, "floor_metrics.csv"), index=False)

    # ---- cell-level summary with bootstrap CIs over instances
    out = []
    for (ds, m, ex, B), g in I.groupby(["dataset", "model", "explainer", "B"]):
        r = dict(dataset=ds, model=m, explainer=ex, B=B, d=g.d.iloc[0], exact_cap=g.exact_cap.iloc[0], n_inst=len(g))
        for k in MK:
            r[f"rr_{k}"] = g[f"rr_{k}"].mean()
        lo, hi = boot_ci(g["rr_J3"]); r["rr_J3_lo"], r["rr_J3_hi"] = lo, hi
        if "ref_J3" in g and g["ref_J3"].notna().any():
            for k in MK: r[f"ref_{k}"] = g[f"ref_{k}"].mean(); r[f"avg5_{k}"] = g[f"avg5_{k}"].mean()
            r["ref_J3_lo"], r["ref_J3_hi"] = boot_ci(g["ref_J3"])
        r["frac_inst_J3_ge_0.8"] = (g["rr_J3"] >= 0.8).mean()
        out.append(r)
    C = pd.DataFrame(out)
    # floor attach
    if len(F):
        Fm = F.groupby(["dataset", "model", "floor"])[MK].mean().reset_index()
        for fl in Fm.floor.unique():
            sub = Fm[Fm.floor == fl].set_index(["dataset", "model"])
            for k in ["J3", "top1", "rbo", "spear"]:
                C[f"{fl}_{k}"] = [sub[k].get((a, b), np.nan) for a, b in zip(C.dataset, C.model)]
        C["adequate_abs"] = C["rr_J3_lo"] >= 0.8
        C["no_worse_than_bg"] = C["rr_J3"] >= C["bg_floor_J3"]
    C.to_csv(os.path.join(RES, "cell_summary.csv"), index=False)
    print(C.groupby(["explainer", "B"])[["rr_J3", "rr_top1", "rr_rbo"]].mean())


if __name__ == "__main__":
    main()
