"""E4 / C3 yardstick summary. Per instance (first n_inst of the cell): d_rerun (mean pairwise 1 - top-3 Jaccard between the R reruns of the
shipped default, for kshap_default and perm500), d_bg (same on exact phi* across background resamples), d_retrain_seed / d_retrain_boot
(same on exact phi* across retrains whose |AUC - AUC of the audited model| <= 0.01). Writes results/yardstick_<tag>.csv (per instance) and
results/yardstick_summary.csv (share d_rerun < d_retrain per group and variant, strict as pre-registered, with instance-bootstrap CI; ties and the <= share reported separately as a sensitivity).
usage: PYTHONPATH=. python3 scripts/summarize_yard.py --cells CELL ... [--tag R20]"""
import argparse, glob, json, os
import numpy as np, pandas as pd
from shapaudit import cells, metrics

ap = argparse.ArgumentParser(); ap.add_argument("--cells", nargs="+", required=True); ap.add_argument("--tag", default="R20")
ap.add_argument("--out", default="results"); ap.add_argument("--nboot", type=int, default=2000); ap.add_argument("--k", type=int, default=3)
a = ap.parse_args()
K = a.k

def pair_dis(sets):
    """sets (n, V, d) boolean top-k masks over V variants; mean pairwise 1 - Jaccard per row."""
    if sets.shape[1] < 2: return np.full(sets.shape[0], np.nan)
    return 1 - metrics.pairwise_jaccard(sets)

rows = []
for cell in a.cells:
    W = f"{cells.WORK}/cells/{cell}"; Y = f"{cells.WORK}/yard/{cell}"
    meta = json.load(open(f"{W}/meta.json")); auc0 = meta["auc"]
    R = np.load(f"{W}/runs_{a.tag}.npz")
    def load(prefix, lo, hi):
        fs = [f"{Y}/{prefix}{v}.npz" for v in range(lo, hi) if os.path.exists(f"{Y}/{prefix}{v}.npz")]
        return [np.load(f) for f in fs]
    V = {"bg": load("bg", 0, 10), "seed": load("seed", 10, 22), "boot": load("boot", 30, 40)}
    n = min(len(z["phi_star"]) for z in V["bg"]) if V["bg"] else 0
    out = {}
    info = {}
    for v, zs in V.items():
        kept = [z for z in zs if v == "bg" or abs(float(z["auc"]) - auc0) <= 0.01]
        info[v] = (len(zs), len(zs) - len(kept), (min(float(z["auc"]) for z in zs), max(float(z["auc"]) for z in zs)) if zs else (np.nan, np.nan))
        if kept:
            S = np.stack([metrics.topk_mask(z["phi_star"], K) for z in kept], 1)    # (n, V, d)
            out[v] = pair_dis(S)
    for arm, key in (("kshap_default", "phi/kshap_default/x1"), ("perm", "phi/perm/perm500")):
        ph = R[key][:n]; out[f"rerun_{arm}"] = pair_dis(metrics.topk_mask(ph, K))
    for i in range(n):
        rows.append(dict(cell=cell, inst=int(R["inst"][i]), d_rerun_kshap_default=out["rerun_kshap_default"][i], d_rerun_perm=out["rerun_perm"][i],
                         d_bg=out["bg"][i] if "bg" in out else np.nan, d_retrain_seed=out["seed"][i] if "seed" in out else np.nan,
                         d_retrain_boot=out["boot"][i] if "boot" in out else np.nan, n_bg=info["bg"][0], n_retrain_seed=info["seed"][0] - info["seed"][1],
                         n_retrain_boot=info["boot"][0] - info["boot"][1], n_dropped_by_equal_acc_filter_seed=info["seed"][1], n_dropped_by_equal_acc_filter_boot=info["boot"][1],
                         auc_audited=auc0, auc_range_seed=f"{info['seed'][2][0]:.3f}-{info['seed'][2][1]:.3f}", auc_range_boot=f"{info['boot'][2][0]:.3f}-{info['boot'][2][1]:.3f}"))
Y = pd.DataFrame(rows); Y.to_csv(f"{a.out}/yardstick_{a.tag}.csv", index=False)

rng = np.random.default_rng(0); S = []
Y["group"] = Y.cell.str.replace(r"_s\d+$", "", regex=True)
for g, G in Y.groupby("group"):
    for arm in ("kshap_default", "perm"):
        for ref in ("d_bg", "d_retrain_seed", "d_retrain_boot"):
            H = G[[f"d_rerun_{arm}", ref]].dropna()
            if not len(H): continue
            lt = (H[f"d_rerun_{arm}"] < H[ref] - 1e-12).values.astype(float); tie = (np.abs(H[f"d_rerun_{arm}"] - H[ref]) <= 1e-12).values.astype(float)
            bs = np.array([lt[rng.integers(0, len(lt), len(lt))].mean() for _ in range(a.nboot)])
            S.append(dict(group=g, arm=arm, reference=ref, n_inst=len(H), share_rerun_lt_ref=lt.mean(), ci_lo=np.percentile(bs, 2.5), ci_hi=np.percentile(bs, 97.5),
                          share_ties=tie.mean(), share_rerun_le_ref_sensitivity=(lt + tie).mean(), mean_d_rerun=H[f"d_rerun_{arm}"].mean(), mean_d_ref=H[ref].mean(),
                          supported=bool(lt.mean() >= 0.75 and np.percentile(bs, 2.5) >= 0.6)))
S = pd.DataFrame(S); S.to_csv(f"{a.out}/yardstick_summary.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); print(S.round(3).to_string())
