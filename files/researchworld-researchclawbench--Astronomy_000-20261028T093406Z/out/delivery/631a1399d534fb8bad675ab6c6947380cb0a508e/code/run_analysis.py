"""Bayesian superradiance exclusion of ultralight bosons from BH (M, a*) posteriors.

Usage: python3 code/run_analysis.py [--data DIR] [--out DIR]
Writes everything to outputs/ (CSV / JSON / NPZ). Deterministic (seeded).
"""
import argparse, json, hashlib, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sr

p = argparse.ArgumentParser()
p.add_argument("--data", default="/initial-state/inputs/2")
p.add_argument("--rate", choices=["detweiler", "leaver"], default="detweiler",
               help="growth-rate model: analytic Detweiler, or Detweiler x tabulated Leaver correction")
p.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs"))
args = p.parse_args()
OUT = os.path.abspath(args.out)
os.makedirs(OUT, exist_ok=True)
TAG = "" if args.rate == "detweiler" else "_leaver"
RATE = sr.gamma_detweiler if args.rate == "detweiler" else sr.make_calibrated_rate(os.path.join(OUT, "rate_table.npz"))
rng = np.random.default_rng(20261028)

BH = {"M33_X-7": "M33_X-7_samples.dat", "IRAS_09149-6206": "IRAS_09149-6206_samples.dat"}
S = {k: np.loadtxt(os.path.join(args.data, v)) for k, v in BH.items()}
prov = {v: hashlib.sha256(open(os.path.join(args.data, v), "rb").read()).hexdigest() for v in BH.values()}

T0 = 4.5e7                                   # yr, Salpeter time (paper_000, paper_001)
MU = np.logspace(-21, -10, 441)              # eV
CLS = {"50%": 0.50, "68%": 0.68, "95%": 0.95, "99.7%": 0.997}


def pex_curve(samp, t_yr=T0, fa=np.inf, mu=MU, **kw):
    M, a = samp[:, 0][:, None], samp[:, 1][:, None]
    ex = sr.excluded(mu[None, :], M, a, t_yr, fa_eV=fa, rate=RATE, **kw)
    return ex.mean(axis=0)


def windows(mu, pex, cl):
    """Contiguous mu intervals with P_ex >= cl; edges linearly interpolated in (log mu, P_ex)."""
    lm = np.log10(mu)
    on = pex >= cl
    res, i, n = [], 0, len(mu)
    while i < n:
        if on[i]:
            j = i
            while j + 1 < n and on[j + 1]:
                j += 1
            lo = lm[i] if i == 0 else lm[i - 1] + (cl - pex[i - 1]) / (pex[i] - pex[i - 1]) * (lm[i] - lm[i - 1])
            hi = lm[j] if j == n - 1 else lm[j] + (pex[j] - cl) / (pex[j] - pex[j + 1]) * (lm[j + 1] - lm[j])
            res.append((10 ** lo, 10 ** hi))
            i = j + 1
        else:
            i += 1
    return res


def combine(pex_list):
    pal = np.prod([1.0 - p for p in pex_list], axis=0)
    return 1.0 - pal


# ---------------------------------------------------------------- 1. baseline P_ex(mu)
t_start = time.time(); print("start", flush=True)
base = {k: pex_curve(v) for k, v in S.items()}
comb = combine(list(base.values()))
nS = {k: len(v) for k, v in S.items()}
# binomial MC error (posterior sample size) for each curve
err = {k: np.sqrt(np.maximum(base[k] * (1 - base[k]), 1e-12) / nS[k]) for k in S}
# Bayesian posterior of mu: log-uniform prior on [1e-21, 1e-10] eV, likelihood prod_i P_al,i
post = np.prod([1.0 - base[k] for k in S], axis=0)
post = post / np.trapezoid(post, np.log10(MU))
np.savetxt(os.path.join(OUT, f"pex_vs_mu{TAG}.csv"),
           np.column_stack([MU] + [base[k] for k in S] + [err[k] for k in S] + [comb, 1 - comb, post]),
           delimiter=",", comments="",
           header="mu_eV," + ",".join(f"Pex_{k}" for k in S) + "," + ",".join(f"Pex_err_{k}" for k in S)
                  + ",Pex_combined,Pal_combined,posterior_density_per_dex")

# ---------------------------------------------------------------- 2. windows (+ bootstrap MC error on the 95% edges)
def all_windows(curves, comb_curve):
    d = {}
    for k, c in list(curves.items()) + [("combined", comb_curve)]:
        d[k] = {cl: windows(MU, c, v) for cl, v in CLS.items()}
    return d

W = all_windows(base, comb)
NB = 200
BOOT_CL = (0.5, 0.68, 0.95)
boot = {k: [] for k in S}
for _ in range(NB):
    for k, v in S.items():
        c = pex_curve(v[rng.integers(0, len(v), len(v))])
        boot[k].append([windows(MU, c, cl) for cl in BOOT_CL])
bootstats = {}
for k in S:
    bootstats[k] = {}
    for ic, cl in enumerate(BOOT_CL):
        lo = [w[ic][0][0] for w in boot[k] if w[ic]]; hi = [w[ic][-1][1] for w in boot[k] if w[ic]]
        bootstats[k][f"{cl:.2f}"] = {"frac_bootstraps_with_window": len(lo) / NB,
            "lo_16_50_84": np.percentile(lo, [16, 50, 84]).tolist() if lo else None,
            "hi_16_50_84": np.percentile(hi, [16, 50, 84]).tolist() if hi else None}

# ---------------------------------------------------------------- 3. point estimate vs full posterior
pe = {}
for k, v in S.items():
    med = np.median(v, axis=0)
    ind = sr.excluded(MU, med[0], med[1], T0, rate=RATE).astype(float)          # step function: 0/1
    pe[k] = {"median_M": float(med[0]), "median_a": float(med[1]),
             "windows_point_estimate": windows(MU, ind, 0.5)}
    # point estimate at +-1 sigma in spin (marginal, ignoring covariance)
    lo_a, hi_a = np.percentile(v[:, 1], [16, 84])
    pe[k]["windows_point_a_lo"] = windows(MU, sr.excluded(MU, med[0], lo_a, T0, rate=RATE).astype(float), 0.5)
    pe[k]["windows_point_a_hi"] = windows(MU, sr.excluded(MU, med[0], hi_a, T0, rate=RATE).astype(float), 0.5)
    np.savetxt(os.path.join(OUT, f"point_estimate_indicator_{k}{TAG}.csv"), np.column_stack([MU, ind]),
               delimiter=",", comments="", header="mu_eV,excluded_at_median_M_a")

# ---------------------------------------------------------------- 4. sensitivity
variants = {
    "baseline (t=4.5e7 yr, l=1-5, no self-int.)": dict(),
    "t=1e6 yr": dict(t_yr=1e6),
    "t=1e7 yr": dict(t_yr=1e7),
    "t=1.38e10 yr (Hubble)": dict(t_yr=1.38e10),
    "levels l=m=1 only": dict(levels=(1,)),
    "levels l=m=1,2": dict(levels=(1, 2)),
    "min 100 e-folds (A&D)": dict(efold_min=100.0),
}
sens = {}
for name, kw in variants.items():
    cur = {k: pex_curve(v, **kw) for k, v in S.items()}
    cc = combine(list(cur.values()))
    sens[name] = {k: windows(MU, c, 0.95) for k, c in list(cur.items()) + [("combined", cc)]}

# ---------------------------------------------------------------- 5. self-interaction: (mu, f_a) exclusion region
FA_GEV = np.logspace(10, 19.5, 77)
MU2 = np.logspace(-21, -10, 221)
def pex_grid(samp, kappa=1.0, t_yr=T0):
    out = np.zeros((len(FA_GEV), len(MU2)))
    M, a = samp[:, 0], samp[:, 1]
    for j, mu in enumerate(MU2):
        for i, fa in enumerate(FA_GEV):
            out[i, j] = sr.excluded(mu, M, a, t_yr, fa_eV=fa * sr.GEV, kappa=kappa, rate=RATE).mean()
    return out
def fa_min(grid, cl):
    """smallest f_a [GeV] at which P_ex >= cl for each mu (nan if none)."""
    res = np.full(grid.shape[1], np.nan)
    for j in range(grid.shape[1]):
        ok = np.where(grid[:, j] >= cl)[0]
        if len(ok):
            res[j] = FA_GEV[ok[0]]
    return res
grids = {}
for kap_name, kap in [("kappa1", 1.0), ("kappa0.1", 0.1), ("kappa10", 10.0)]:
    g = {}
    for k, v in S.items():
        sub = v if len(v) <= 3000 else v[rng.choice(len(v), 3000, replace=False)]
        g[k] = pex_grid(sub, kappa=kap)
    grids[kap_name] = g
np.savez_compressed(os.path.join(OUT, f"pex_grid_mu_fa{TAG}.npz"), mu_eV=MU2, fa_GeV=FA_GEV,
                    **{f"{kn}_{k}": g[k] for kn, g in grids.items() for k in S},
                    **{f"{kn}_combined": 1 - np.prod([1 - g[k] for k in S], axis=0) for kn, g in grids.items()})
fam = {}
for kn, g in grids.items():
    cg = 1 - np.prod([1 - g[k] for k in S], axis=0)
    fam[kn] = {k: fa_min(g[k], 0.95) for k in S}
    fam[kn]["combined"] = fa_min(cg, 0.95)
cols, hdr = [MU2], ["mu_eV"]
for kn in fam:
    for k, v in fam[kn].items():
        cols.append(v); hdr.append(f"fa_min95_GeV_{kn}_{k}")
np.savetxt(os.path.join(OUT, f"fa_min_95_vs_mu{TAG}.csv"), np.column_stack(cols), delimiter=",", comments="", header=",".join(hdr))

# ---------------------------------------------------------------- 6. summary
summ = dict(
    rate_model=args.rate, inputs_sha256=prov, n_samples=nS, t_baseline_yr=T0, n_bootstrap=NB, runtime_s=time.time() - t_start,
    windows_baseline_eV=W, bootstrap_95_edges=bootstats, point_estimate=pe, sensitivity_95=sens,
    fa_min_95_summary={kn: {k: {"min_GeV": (float(np.nanmin(v)) if np.isfinite(v).any() else None)}
                            for k, v in fam[kn].items()} for kn in fam},
)
json.dump(summ, open(os.path.join(OUT, f"summary{TAG}.json"), "w"), indent=1, default=float)
print(json.dumps({"windows_95": {k: W[k]["95%"] for k in W}}, indent=1, default=float))
print("HUTIAN_WAKE: run_analysis finished", flush=True)
