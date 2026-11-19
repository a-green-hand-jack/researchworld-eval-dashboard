"""Stage 2: aggregate per-instance tables into the result tables (instance = unit of resampling).

usage: python3 analysis/summarize.py [tables_dir]
Outputs (CSV, in tables_dir):
  budget_curve.csv   per cell x explainer x budget: mean of each measure over instances with 95% bootstrap CI
  adequacy.csv       fraction of instances whose single run reproduces the reference top-k set with prob >= tau
                     (k in {1,3,5}, tau in {0.8,0.9,0.95}), Wilson 95% CI
  slopes.csv         log-log slope of RMS error vs rows evaluated (global and consecutive), bootstrap CI over instances
  margin_bins.csv    adequacy vs margin tercile (reference gap between rank k and k+1) per cell x explainer x budget
  snr_bins_cell.csv  the same per cell (pooled over its budgets)
  snr_bins.csv       empirical top-k match probability against z = reference gap / run-to-run sd of the gap (pooled over cells and budgets)
  standards.csv      pairwise top-k agreement / distance between retrained models, redrawn backgrounds, random instances
"""
import os, sys
from scipy.stats import norm
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import metrics as M

T = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results", "tables")
rng = np.random.RandomState(12345)
pi = pd.read_csv(f"{T}/per_instance.csv")
G = ["dataset", "model", "d", "explainer", "budget_idx", "budget"]
meas = [c for c in pi.columns if c.startswith(("blowup_frac", "relerr_mean", "relerr_med", "bias_norm", "sd_norm", "cos_ref", "kendall_ref", "rbo_ref",
                                                 "match_ref", "jac_ref", "pair_match", "pair_jac", "nogueira", "signflip"))]


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


rows = []
for key, g in pi.groupby(G):
    r = dict(zip(G, key)); r["rows"] = g.rows.mean(); r["n_inst"] = len(g); r["frac_space"] = g.frac_space.mean()
    for m in meas:
        v = g[m].values
        mu, lo, hi = M.boot_ci(v, rng, B=1000)
        r[m], r[m + "_lo"], r[m + "_hi"] = mu, lo, hi
    rows.append(r)
pd.DataFrame(rows).to_csv(f"{T}/budget_curve.csv", index=False)

# adequacy: fraction of instances with P_runs[top-k set == reference] >= tau
ad = []
for key, g in pi.groupby(G):
    for k in (1, 3, 5):
        c = f"match_ref_k{k}"
        if c not in g or g[c].isna().all():
            continue
        for tau in (0.8, 0.9, 0.95):
            kk = int((g[c] >= tau - 1e-12).sum()); n = len(g)
            lo, hi = wilson(kk, n)
            ad.append(dict(zip(G, key), rows=g.rows.mean(), k=k, tau=tau, frac_adequate=kk / n, lo=lo, hi=hi, n_inst=n))
pd.DataFrame(ad).to_csv(f"{T}/adequacy.csv", index=False)

# slopes of the typical relative error (mean over instances of the per-instance median over runs) vs rows evaluated.
# Kernel SHAP: fit only where the budget is <= 50% of the 2^d-2 non-trivial coalitions (beyond that the library
# enumerates most of the space and the error is no longer Monte-Carlo-like); all budgets for Permutation.
sl = []
for key, g in pi.groupby(["dataset", "model", "d", "explainer"]):
    piv = g.pivot(index="inst", columns="budget_idx", values="relerr_med")
    rws = g.groupby("budget_idx").rows.mean().values
    fs = g.groupby("budget_idx").frac_space.mean().values
    n = len(piv)
    def curve(ix):
        return piv.values[ix].mean(0)
    full = curve(np.arange(n))
    ok = (full > 1e-9) & (np.where(np.isnan(fs), 0, fs) <= 0.5)
    if ok.sum() < 3:
        continue
    lx = np.log(rws)
    def slope(c, mask):
        return np.polyfit(lx[mask], np.log(c[mask]), 1)[0]
    bs = np.array([slope(curve(rng.randint(0, n, n)), ok) for _ in range(500)])
    sl.append(dict(zip(["dataset", "model", "d", "explainer"], key), scope="global", n_budgets=int(ok.sum()),
                   slope=slope(full, ok), lo=np.quantile(bs, .025), hi=np.quantile(bs, .975)))
    idx = np.where(full > 1e-9)[0]
    for a, b in zip(idx[:-1], idx[1:]):
        if lx[b] == lx[a]:  # two nominal budgets that map to the same number of evaluated rows (Permutation at the minimum): no slope
            continue
        s_ = np.log(full[b] / full[a]) / (lx[b] - lx[a])
        sl.append(dict(zip(["dataset", "model", "d", "explainer"], key), scope=f"{int(rws[a])}->{int(rws[b])}", n_budgets=2, slope=s_, lo=np.nan, hi=np.nan))
pd.DataFrame(sl).to_csv(f"{T}/slopes.csv", index=False)

# margin dependence: terciles of reference margin (rank k vs k+1), within cell
mb = []
for key, g in pi.groupby(G):
    for k in (1, 3, 5):
        c, mc = f"match_ref_k{k}", f"margin_k{k}"
        if c not in g or g[c].isna().all():
            continue
        q = pd.qcut(g[mc].rank(method="first"), 3, labels=["low", "mid", "high"])
        for lab in ["low", "mid", "high"]:
            s = g[q == lab]
            mu, lo, hi = M.boot_ci(s[c].values, rng, B=500)
            mb.append(dict(zip(G, key), k=k, margin_tercile=lab, n_inst=len(s), margin_mean=s[mc].mean(), match_ref=mu, lo=lo, hi=hi))
pd.DataFrame(mb).to_csv(f"{T}/margin_bins.csv", index=False)

# pred_normal = mean Phi(z) of the bin: the match probability if only the swap of ranks k and k+1 mattered and the gap were normal
# signal-to-noise of the decisive gap: z = (|phi*|_(k) - |phi*|_(k+1)) / sd over runs of that gap; empirical match probability by z bin
sn = []
bins = [0, 0.5, 1, 1.5, 2, 3, 5, np.inf]
for k in (1, 3, 5):
    if f"margin_abs_k{k}" not in pi:
        continue
    q = pi.dropna(subset=[f"match_ref_k{k}"]).copy()
    q["z"] = q[f"margin_abs_k{k}"] / (q[f"gap_sd_k{k}"] + 1e-12)
    q["zbin"] = pd.cut(q["z"], bins, right=False)
    q["cluster"] = q.dataset + "/" + q.model + "/" + q.inst.astype(str)   # one instance appears at several budgets: resample instances
    for (ex, zb), g in q.groupby(["explainer", "zbin"], observed=True):
        cl = g.groupby("cluster")[f"match_ref_k{k}"].agg(["sum", "count"])
        ix = rng.randint(0, len(cl), (500, len(cl)))
        bs = cl["sum"].values[ix].sum(1) / cl["count"].values[ix].sum(1)
        sn.append(dict(explainer=ex, k=k, z_bin=str(zb), n=len(g), n_clusters=len(cl), z_mean=g.z.mean(),
                       pred_normal=norm.cdf(g.z).mean(), match_ref=g[f"match_ref_k{k}"].mean(), lo=np.quantile(bs, .025), hi=np.quantile(bs, .975)))
pd.DataFrame(sn).to_csv(f"{T}/snr_bins.csv", index=False)

# the same per cell (pooled over the cell's budgets; the instance is the resampling unit)
sc_ = []
for k in (1, 3, 5):
    if f"margin_abs_k{k}" not in pi:
        continue
    q = pi.dropna(subset=[f"match_ref_k{k}"]).copy()
    q["z"] = q[f"margin_abs_k{k}"] / (q[f"gap_sd_k{k}"] + 1e-12)
    q["zbin"] = pd.cut(q["z"], bins, right=False)
    for (ds_, mo_, ex, zb), g in q.groupby(["dataset", "model", "explainer", "zbin"], observed=True):
        cl = g.groupby("inst")[f"match_ref_k{k}"].agg(["sum", "count"])
        ix = rng.randint(0, len(cl), (500, len(cl)))
        bs = cl["sum"].values[ix].sum(1) / cl["count"].values[ix].sum(1)
        sc_.append(dict(dataset=ds_, model=mo_, explainer=ex, k=k, z_bin=str(zb), n=len(g), n_instances=len(cl), pred_normal=norm.cdf(g.z).mean(), match_ref=g[f"match_ref_k{k}"].mean(),
                        lo=np.quantile(bs, .025), hi=np.quantile(bs, .975)))
pd.DataFrame(sc_).to_csv(f"{T}/snr_bins_cell.csv", index=False)

# comparison standards
sf = f"{T}/standards_instance.csv"
if os.path.exists(sf):
    st = pd.read_csv(sf)
    out = []
    for key, g in st.groupby(["dataset", "model", "d", "standard", "k"]):
        r = dict(zip(["dataset", "model", "d", "standard", "k"], key)); r["n_inst"] = len(g)
        for m in ["pair_match", "pair_jac", "nogueira", "pair_reldist"]:
            mu, lo, hi = M.boot_ci(g[m].values, rng, B=1000)
            r[m], r[m + "_lo"], r[m + "_hi"] = mu, lo, hi
        out.append(r)
    pd.DataFrame(out).to_csv(f"{T}/standards.csv", index=False)
print("summaries written to", T)
