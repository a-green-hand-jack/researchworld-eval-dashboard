"""Calibration of the budget scale B from real base -> fine-tune pairs of the Open LLM Leaderboard `contents` snapshot (data_proc/ollb_m6_contents.csv).
Pair = non-merged, non-flagged child whose `Base Model` is another model on the board (not pretrained/merge types as children). Gain = child - base per benchmark
(normalised board scale, points). Writes OUT/calibration.csv (one row per child, base, task) and OUT/calibration_summary.csv
(per parent-size bucket: share of (child, task) gains >= each B on the grid, and the per-child largest single-task gain; CI = bootstrap over base models, 2000 draws, seed 20260102).
usage: run_calibration.py OUTDIR"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice.boards import BEN6, DP, ollb_family
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
d0 = pd.read_csv(os.path.join(DP, "ollb_m6_contents.csv"))
d = d0.sort_values("main_slice", ascending=False, kind="stable").drop_duplicates("fullname").reset_index(drop=True)  # one row per model name (main slice first)
idx = d.set_index("fullname")
sig = d[d.main_slice][BEN6].std()
okchild = d.Type.isin(["🔶 fine-tuned on domain-specific datasets", "💬 chat models (RLHF, DPO, IFT, ...)"]) & ~d.Merged & ~d.Flagged.astype(bool)
ch = d[okchild & (d["Base Model"] != d.fullname) & d["Base Model"].isin(idx.index)]
BUCKETS = [(0, 3, "<3B"), (3, 9, "3-9B"), (9, 20, "9-20B"), (20, 40, "20-40B"), (40, 1e9, ">40B")]
def bucket(p):
    for lo, hi, n in BUCKETS:
        if lo <= p < hi: return n
    return "unknown"
fam = dict(zip(d.fullname, ollb_family(d)[1]))
sig = d0[d0.main_slice][BEN6].std()
nch = ch["Base Model"].value_counts()
rows = []
for _, r in ch.iterrows():
    b = idx.loc[r["Base Model"]]
    for t in BEN6:
        rows.append(dict(child=r.fullname, base=r["Base Model"], task=t, gain=r[t] - b[t], gain_raw=r[t + " Raw"] - b[t + " Raw"], gain_sigma=(r[t] - b[t]) / sig[t],
                         parent_params=b["#Params (B)"], child_params=r["#Params (B)"], size_bucket=bucket(b["#Params (B)"]) if b["#Params (B)"] > 0 else "unknown",
                         base_family=fam[r["Base Model"]], n_children_base=int(nch[r["Base Model"]]), child_type=r.Type, base_type=b.Type, child_date=r["Submission Date"]))
cal = pd.DataFrame(rows); cal.to_csv(f"{out}/calibration.csv", index=False)
# summary
GRID = [1, 2, 5, 10, 20, 30]
rng = np.random.default_rng(20260102); summ = []
for bk in [b[2] for b in BUCKETS]:
    g = cal[cal.size_bucket == bk]
    if g.empty: continue
    bases = g.base.unique()
    mx = g.groupby("child").gain.max()
    def stats(gg):
        mxx = gg.groupby("child").gain.max()
        return {**{f"share_task_gain_ge_{B}": (gg.gain >= B).mean() for B in GRID}, **{f"share_child_maxgain_ge_{B}": (mxx >= B).mean() for B in GRID},
                "median_task_gain": gg.gain.median(), "q90_task_gain": gg.gain.quantile(0.9), "median_child_maxgain": mxx.median()}
    est = stats(g); by = {b: g[g.base == b] for b in bases}
    boots = [stats(pd.concat([by[b] for b in rng.choice(bases, len(bases))])) for _ in range(2000)]
    for k, v in est.items():
        bs = np.array([x[k] for x in boots])
        summ.append(dict(size_bucket=bk, statistic=k, value=v, ci_lo=np.percentile(bs, 2.5), ci_hi=np.percentile(bs, 97.5), n_children=g.child.nunique(), n_bases=len(bases)))
pd.DataFrame(summ).to_csv(f"{out}/calibration_summary.csv", index=False)
print(cal.groupby("size_bucket").agg(children=("child", "nunique"), bases=("base", "nunique"), med=("gain", "median")).to_string())
