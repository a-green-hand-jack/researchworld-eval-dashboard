"""C3 / H8: regression vs relaxed-exposure Hajek (several delta) vs DM vs exact HT, same draws (grid e3 + e3c).
Writes results/summary/c3_pairs.csv (one row per cell x d x competitor) and prints win/tie/loss counts.
'win' = paired-bootstrap 95% CI of RMSE(REG-L) - RMSE(competitor) lies below 0 (REG-L better), 'loss' above 0, else 'tie'.
Hajek delta rules: 'declared' = smallest delta in the grid with expected exposed units per arm >= 50 (needs only n, d, p);
'oracle' = delta with the smallest RMSE in the cell (uses the truth; an upper bound for the family)."""
import numpy as np
import pandas as pd
from scipy.stats import binom

B = 400
rng = np.random.default_rng(0)
a = pd.read_parquet("results/raw/e3.parquet")
c = pd.read_parquet("results/raw/e3c.parquet")
key = ["graph.d", "out.kappa", "out.shape", "design.p", "rep"]
c = c[key + ["HAJEK-r0.1", "HAJEK-r0.75"]]
df = a.merge(c, on=key, validate="one_to_one")
DELTAS = [0.0, 0.1, 0.25, 0.5, 0.75]
col = {0.0: "HAJEK", 0.1: "HAJEK-r0.1", 0.25: "HAJEK-r0.25", 0.5: "HAJEK-r0.5", 0.75: "HAJEK-r0.75"}
cells = ["graph.d", "out.kappa", "out.shape", "design.p"]


def declared_delta(d, p, n=2000, m=50):
    for dl in DELTAS:
        k1 = np.ceil((1 - dl) * d - 1e-9); k0 = np.floor(dl * d + 1e-9)
        q = min(p * binom.sf(k1 - 1, d, p), (1 - p) * binom.cdf(k0, d, p))
        if n * q >= m:
            return dl
    return DELTAS[-1]


rows = []
for key_, g in df.groupby(cells):
    d, kap, shp, p = key_
    err = {"REG-L": g["REG-L"] - g["tau"], "REG-Q": g["REG-Q"] - g["tau"], "REG-O": g["REG-O"] - g["tau"], "DM": g["DM"] - g["tau"]}
    for dl in DELTAS:
        err[f"H{dl:g}"] = g[col[dl]] - g["tau"]
    E = pd.DataFrame(err).to_numpy(); names = list(err)
    se2 = E ** 2
    rm = np.sqrt(np.nanmean(se2, 0))
    dl_decl = declared_delta(d, p)
    dl_orc = DELTAS[int(np.argmin([rm[names.index(f"H{x:g}")] for x in DELTAS]))]
    err["H-declared"] = err[f"H{dl_decl:g}"]; err["H-oracle"] = err[f"H{dl_orc:g}"]
    names = list(err); se2 = pd.DataFrame(err).to_numpy() ** 2
    idx = rng.integers(0, len(g), (B, len(g)))
    iL = names.index("REG-L")
    for j, nm in enumerate(names):
        if nm == "REG-L":
            continue
        diff = np.sqrt(np.nanmean(se2[:, iL][idx], 1)) - np.sqrt(np.nanmean(se2[:, j][idx], 1))
        lo, hi = np.quantile(diff, [0.025, 0.975])
        rows.append(dict(d=d, kappa=kap, shape=shp, p=p, competitor=nm, rmse_regL=float(np.sqrt(np.nanmean(se2[:, iL]))),
                         rmse_comp=float(np.sqrt(np.nanmean(se2[:, j]))), diff_lo=lo, diff_hi=hi,
                         outcome="win" if hi < 0 else ("loss" if lo > 0 else "tie"),
                         delta_declared=dl_decl, delta_oracle=dl_orc, n_rep=len(g)))
out = pd.DataFrame(rows)
out.to_csv("results/summary/c3_pairs.csv", index=False)
print(out.groupby(["competitor", "outcome"]).size().unstack(fill_value=0))
print(out.groupby(["competitor"])[["delta_declared"]].first())
