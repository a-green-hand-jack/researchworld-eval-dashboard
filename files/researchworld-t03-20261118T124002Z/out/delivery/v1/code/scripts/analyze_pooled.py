"""Pooled analysis of the tidy files: C1 (hidden tail), C2 (B*(x)), C5 (bias vs noise) per group = dataset x subset x model (seeds pooled).
Verdict rules are those of docs/PROTOCOL.md section 4. Writes results/verdicts_<tag>.csv, instances_<tag>.csv, bias_variance_<tag>.csv.
Cluster bootstrap: resample model seeds, then instances within each drawn seed (2000 resamples)."""
import argparse, glob, os, re
import numpy as np, pandas as pd
from scipy.stats import spearmanr, rankdata

ap = argparse.ArgumentParser(); ap.add_argument("--tag", default="R20"); ap.add_argument("--nboot", type=int, default=2000); ap.add_argument("--out", default="results")
a = ap.parse_args()
rng = np.random.default_rng(0)
GRID = {"x0.25": .25, "x0.5": .5, "x1": 1., "x2": 2., "x4": 4., "x16": 16.}
SHIPPED = {"leverage": "x1", "kshap_default": "x1", "kshap_l1off": "x1", "covert_lee": "x1", "perm": "perm500"}   # budget treated as the shipped default of each arm

fs = sorted(glob.glob(f"{a.out}/tidy_*_{a.tag}.csv"))
T = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
m = T.cell.str.extract(r"^(?P<ds>.+)_d(?P<sub>\d+|full)_(?P<model>[a-z_]+?)_s(?P<seed>\d+)$")
T["group"] = m.ds + "_d" + m["sub"] + "_" + m.model; T["seed"] = m.seed.astype(int)

def boot_idx(df):
    """index arrays for one two-level bootstrap resample of rows of df (seed, inst columns)."""
    seeds = df.seed.unique(); out = []
    for s in rng.choice(seeds, len(seeds)):
        ii = np.flatnonzero(df.seed.values == s); out.append(rng.choice(ii, len(ii)))
    return np.concatenate(out)

def boot_ci(df, stat, nb):
    est = stat(df)
    bs = np.array([stat(df.iloc[boot_idx(df)]) for _ in range(nb)])
    bs = bs[np.isfinite(bs)]
    return est, (np.percentile(bs, 2.5), np.percentile(bs, 97.5)) if len(bs) else (np.nan, np.nan)

def auc(score, label):
    label = np.asarray(label, bool)
    if label.all() or (~label).all(): return np.nan
    r = rankdata(score); n1 = label.sum(); n0 = (~label).sum()
    return (r[label].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

verd, inst_rows, bv = [], [], []
for (g, arm), G in T.groupby(["group", "arm"]):
    b = SHIPPED[arm]
    for k in (1, 3, 5):
        D = G[(G.budget == b) & (G.k == k)].reset_index(drop=True)
        if not len(D): continue
        d = int(D.d.iloc[0]); r = D.r.values
        mean_r, ci_r = boot_ci(D, lambda x: x.r.mean(), a.nboot)
        U, ci_U = boot_ci(D, lambda x: (x.r < 0.9).mean(), a.nboot)       # unreliable share at delta = 0.1
        U05, _ = boot_ci(D, lambda x: (x.r < 0.95).mean(), 1)
        nog, ci_nog = boot_ci(D, lambda x: x.nog.mean(), a.nboot)           # rerun repeatability (no phi* needed)
        rbo_m, jacc_m = D.rbo.mean(), D.jacc.mean()
        rho = spearmanr(D.r, D.z_true).statistic if D.r.nunique() > 1 else np.nan
        # plug-in z (Covert-Lee arm only): per-run z against the reliability label of its instance and against the run's own correctness
        auc_inst = auc_run = np.nan
        if arm == "covert_lee":
            zs, labs, oks = [], [], []
            for cell, DD in D.groupby("cell"):
                pz = np.load(f"{a.out}/plugz_{cell}_{a.tag}.npz")
                if f"zplug/{b}/k{k}" not in pz.files: continue
                idx = {int(i): j for j, i in enumerate(pz["inst"])}
                rows = np.array([idx[int(i)] for i in DD.inst])
                z = pz[f"zplug/{b}/k{k}"][rows]; ok = pz[f"ok/{b}/k{k}"][rows]
                zs.append(z.ravel()); oks.append(ok.ravel()); labs.append(np.repeat((DD.r.values >= 0.9), z.shape[1]))
            if zs:
                zs, oks, labs = map(np.concatenate, (zs, oks, labs))
                auc_inst, auc_run = auc(zs, labs), auc(zs, oks)
        vd = None
        if k == 3 and arm in ("kshap_default", "perm"):
            lo_U = ci_U[0]
            if mean_r < 0.90: vd = "a_unreliable_at_default"
            elif U >= 0.05 and lo_U > 0: vd = "b_supported"
            elif U < 0.05: vd = "c_not_supported"
            else: vd = "d_inconclusive"
        # C5: bias share among unreliable instances (d >= 11)
        bias_share = ci5 = (np.nan, np.nan)
        if d >= 11:
            def sh(x):
                u = x[x.r < 0.9]
                return (~u.mean_ok).mean() if len(u) else np.nan
            bias_share, ci5 = boot_ci(D, sh, a.nboot)
            bv.append(dict(group=g, arm=arm, d=d, k=k, n_inst=len(D), n_unreliable=int((D.r < 0.9).sum()), bias_share=bias_share, ci_lo=ci5[0], ci_hi=ci5[1],
                           mean_rel_bias=D.rel_bias.mean()))
        verd.append(dict(group=g, arm=arm, k=k, budget=b, d=d, n=len(D), n_seeds=D.seed.nunique(), mean_r=mean_r, r_lo=ci_r[0], r_hi=ci_r[1],
                         U_delta10=U, U_lo=ci_U[0], U_hi=ci_U[1], U_delta05=U05, nog=nog, nog_lo=ci_nog[0], nog_hi=ci_nog[1], rbo=rbo_m, jacc=jacc_m, spearman_r_ztrue=rho, auc_plugz_instance=auc_inst, auc_plugz_run=auc_run,
                         C1_outcome=vd, C5_bias_share=bias_share if np.isscalar(bias_share) else np.nan))   # bias share of unreliable instances, d>=11, any arm
        # C2: B*(x) over the x-grid
        if True:
            P = G[(G.k == k) & G.budget.isin(GRID)].copy(); P["mult"] = P.budget.map(GRID)
            for (cell, i), H in P.groupby(["cell", "inst"]):
                H = H.sort_values("mult")
                for dl in (0.05, 0.1):
                    hit = H[H.r >= 1 - dl]
                    z1 = H[H.budget == "x1"]
                    inst_rows.append(dict(group=g, cell=cell, inst=i, arm=arm, k=k, delta=dl, Bstar_mult_emp=hit.mult.iloc[0] if len(hit) else np.nan,
                                          censored=not len(hit), z_true_x1=float(z1.z_true.iloc[0]) if len(z1) else np.nan, gap=float(H.gap.iloc[0]),
                                          nvar=int(H.nvar.iloc[0]), d=int(H.d.iloc[0])))
V = pd.DataFrame(verd); I = pd.DataFrame(inst_rows)
if len(I):
    I["Bstar_mult_pred"] = np.nan
    for (g, arm, k, dl), H in I.groupby(["group", "arm", "k", "delta"]):
        ok = ~H.censored & (H.z_true_x1 > 0)
        c = np.median(H.Bstar_mult_emp[ok] * H.z_true_x1[ok] ** 2) if ok.any() else np.nan      # B*/B0 = c / z^2, c fitted once per group
        I.loc[H.index, "Bstar_mult_pred"] = c / H.z_true_x1 ** 2
        sub = H[ok]
        rho = spearmanr(sub.Bstar_mult_emp, c / sub.z_true_x1 ** 2).statistic if len(sub) > 3 and sub.Bstar_mult_emp.nunique() > 1 else np.nan
        lg = np.log2(sub.Bstar_mult_emp)
        V.loc[(V.group == g) & (V.arm == arm) & (V.k == k), f"C2_spearman_d{int(dl*100):02d}"] = rho
        V.loc[(V.group == g) & (V.arm == arm) & (V.k == k), f"C2_iqr_log2_d{int(dl*100):02d}"] = (np.percentile(lg, 75) - np.percentile(lg, 25)) if len(lg) else np.nan
        V.loc[(V.group == g) & (V.arm == arm) & (V.k == k), f"C2_censored_d{int(dl*100):02d}"] = H.censored.mean()
os.makedirs(a.out, exist_ok=True)
V.to_csv(f"{a.out}/verdicts_{a.tag}.csv", index=False); I.to_csv(f"{a.out}/instances_{a.tag}.csv", index=False)
if bv: pd.DataFrame(bv).to_csv(f"{a.out}/bias_variance_{a.tag}.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(V[V.k == 3].round(3).to_string())
