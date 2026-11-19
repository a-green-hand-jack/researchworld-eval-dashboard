"""C5 three-way split of the unreliable instances of the shipped KernelSHAP default (k=3, delta=0.1: r_3 < 0.9 at the x1 budget), per group = dataset x d x model.
An instance is unreliable if r < 0.9. mean_ok = the top-k of the mean of the R=20 default runs equals the exact top-k.
  trunc_bias   : mean_ok False under the default and True under the paired kshap_l1off arm (same instance, same budget): truncation (l1_reg) bias
  other_bias   : mean_ok False under the default and under l1off: expected attribution wrong without l1 being the cause (near-ties at finite R, residual estimator bias)
  noise        : mean_ok True under the default: the mean is right and the runs scatter; split by z_true = gap / sd of the gap at x1 (descriptive convention, threshold 1):
     noise_gap_lt_sd (selection instability: run scatter exceeds the gap) and noise_gap_ge_sd (sampling variance with a resolvable gap)
trunc + other + noise = 1. CIs: cluster bootstrap over model seeds, then instances within seeds (2000 resamples), shares recomputed per resample.
Writes results/c5_split_R20.csv. usage: python3 scripts/c5_split.py"""
import glob, numpy as np, pandas as pd
T = pd.concat([pd.read_csv(f, usecols=["cell", "inst", "arm", "budget", "k", "r", "mean_ok", "z_true", "d"]) for f in sorted(glob.glob("results/tidy_*_R20.csv"))], ignore_index=True)
T = T[(T.k == 3) & (T.budget == "x1") & T.arm.isin(["kshap_default", "kshap_l1off"])]
m = T.cell.str.extract(r"^(?P<ds>.+)_d(?P<sub>\d+|full)_(?P<model>[a-z_]+?)_s(?P<seed>\d+)$")
T["group"] = m.ds + "_d" + m["sub"] + "_" + m.model; T["seed"] = m.seed.astype(int)
A = T[T.arm == "kshap_default"].merge(T[T.arm == "kshap_l1off"][["cell", "inst", "mean_ok", "r"]], on=["cell", "inst"], suffixes=("", "_l1off"))
A["mean_ok"] = A.mean_ok.astype(bool); A["mean_ok_l1off"] = A.mean_ok_l1off.astype(bool)
A["unrel"] = A.r < 0.9
rng = np.random.default_rng(0)
def shares(x):
    u = x[x.unrel.values]
    n = len(u)
    if n == 0: return [np.nan] * 5
    tb = (~u.mean_ok.values & u.mean_ok_l1off.values); ob = (~u.mean_ok.values & ~u.mean_ok_l1off.values); nz = u.mean_ok.values
    lo = nz & (u.z_true.values < 1)
    return [tb.mean(), ob.mean(), nz.mean(), (lo).mean(), (nz & ~lo).mean()]
names = ["trunc_bias", "other_bias", "noise", "noise_gap_lt_sd", "noise_gap_ge_sd"]
rows = []
for g, G in A.groupby("group"):
    G = G.reset_index(drop=True); seeds = G.seed.unique()
    pos = {s: np.flatnonzero(G.seed.values == s) for s in seeds}
    est = shares(G)
    bs = []
    for _ in range(2000):
        idx = np.concatenate([rng.choice(pos[s], len(pos[s])) for s in rng.choice(seeds, len(seeds))])
        bs.append(shares(G.iloc[idx]))
    bs = np.array(bs, float)
    ci = [(np.nanpercentile(bs[:, j], 2.5), np.nanpercentile(bs[:, j], 97.5)) if np.isfinite(bs[:, j]).any() else (np.nan, np.nan) for j in range(5)]
    row = dict(group=g, d=int(G.d.iloc[0]), n_seeds=len(seeds), n_inst=len(G), n_unreliable=int(G.unrel.sum()), unreliable_share=G.unrel.mean())
    for j, nm in enumerate(names): row[nm] = est[j]; row[nm + "_lo"] = ci[j][0]; row[nm + "_hi"] = ci[j][1]
    rows.append(row)
R = pd.DataFrame(rows); R.to_csv("results/c5_split_R20.csv", index=False)
pd.set_option("display.width", 250); print(R[["group", "n_inst", "n_unreliable", "unreliable_share"] + names].round(2).to_string())
