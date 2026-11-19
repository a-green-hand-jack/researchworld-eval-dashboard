"""E3/E4: (a) single-run self-certification from permutation-sampling in-run statistics; (b) 'two half-budget runs'
agreement certificate; (c) budget splitting: average of k runs of budget m/k vs one run of budget m.
Reads results/core/*.npz.  Writes results/tables/tabF_cert*.csv, tabG_split*.csv, results/figs/fig_cert*.pdf"""
import os, sys, glob
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from data import RESULTS
from shapsim import _order

suffix = "_quick" if "--quick" in sys.argv else ""
TAB = os.path.join(RESULTS, "tables"); FIG = os.path.join(RESULTS, "figs")
os.makedirs(TAB, exist_ok=True); os.makedirs(FIG, exist_ok=True)
rng = np.random.default_rng(5)
THRS = [-np.inf, 1.64, 1.96, 2.58, 3.29]


def topk_sets(P, k):
    o = _order(P)[..., :k]
    m = np.zeros(P.shape, bool)
    np.put_along_axis(m, o, True, axis=-1)
    return m


def ratio_boot(num, den, B=1000):
    """cluster bootstrap of sum(num)/sum(den) over clusters (arrays per cluster)."""
    n = len(num)
    idx = rng.integers(0, n, (B, n))
    r = num[idx].sum(1) / np.maximum(den[idx].sum(1), 1e-12)
    return num.sum() / max(den.sum(), 1e-12), np.nanpercentile(r, 2.5), np.nanpercentile(r, 97.5)


files = [f for f in sorted(glob.glob(os.path.join(RESULTS, "core", f"*_*{suffix}.npz")))
         if (suffix == "_quick") == f.endswith("_quick.npz")]
cert_rows, agree_rows, split_rows = [], [], []
clusters = {}   # (dataset, mult, kind('top1'|'top3'), thr) -> lists
for f in files:
    base = os.path.basename(f)[:-4].replace("_quick", "")
    ds, kind = base.split("_")
    Z = np.load(f)
    d, R = int(Z["d"]), int(Z["R"])
    ref = Z["ref_prob"]
    N = ref.shape[0]
    mults = sorted(int(k.split("_")[-1]) for k in Z.files if k.startswith("phi_prob_perm_"))
    ref1 = np.argmax(np.abs(ref), -1)
    ref3 = topk_sets(ref, 3)
    for mult in mults:
        PH = Z[f"phi_prob_perm_{mult}"]   # (N,R,d)
        ZS = Z[f"z_prob_perm_{mult}"]     # (N,R,2)
        if np.all(np.isnan(ZS)):
            continue
        c1 = (np.argmax(np.abs(PH), -1) == ref1[:, None])          # (N,R)
        c3 = (topk_sets(PH, 3) == ref3[:, None, :]).all(-1)
        for tag, c, z in (("top1", c1, ZS[..., 0]), ("top3", c3, ZS[..., 1])):
            for thr in THRS:
                cert = (z >= thr) if np.isfinite(thr) else np.ones_like(c, bool)
                cert &= ~np.isnan(z)
                clusters.setdefault((ds, mult, tag, thr), []).append(
                    (cert.sum(1).astype(float), (cert & c).sum(1).astype(float), np.full(N, R, float), c.sum(1).astype(float)))
        # agreement certificate with two independent runs at this budget (disjoint pairs)
        h = R // 2
        a, b = PH[:, 0:2 * h:2], PH[:, 1:2 * h:2]
        oa, ob = np.argmax(np.abs(a), -1), np.argmax(np.abs(b), -1)
        agree1 = oa == ob
        corr_if = (oa == ref1[:, None])
        avg = 0.5 * (a + b)
        corr_avg = np.argmax(np.abs(avg), -1) == ref1[:, None]
        a3, b3 = topk_sets(a, 3), topk_sets(b, 3)
        agree3 = (a3 == b3).all(-1)
        corr3_avg = (topk_sets(avg, 3) == ref3[:, None, :]).all(-1)
        agree_rows.append(dict(dataset=ds, model=kind, mult_each=mult, cov1=agree1.mean(), prec1=(agree1 & corr_if).sum() / max(agree1.sum(), 1),
                               base1=corr_if.mean(), avg_acc1=corr_avg.mean(),
                               cov3=agree3.mean(), prec3=(agree3 & corr3_avg).sum() / max(agree3.sum(), 1), avg_acc3=corr3_avg.mean()))
    # budget split: average of 2 (and 4) runs of budget m vs single run at 2m (4m)
    for est in ("kernel", "perm"):
        for mult in sorted(int(k.split("_")[-1]) for k in Z.files if k.startswith(f"phi_prob_{est}_")):
            for kk in (2, 4):
                big = mult * kk
                key_big = f"phi_prob_{est}_{big}"
                if key_big not in Z.files:
                    continue
                if est == "kernel" and ds == "pima" and big * d >= 2 ** d - 2:
                    continue
                P_small = Z[f"phi_prob_{est}_{mult}"]
                P_big = Z[key_big]
                h = R // kk
                avg = P_small[:, :h * kk].reshape(N, h, kk, d).mean(2)
                e_avg = np.linalg.norm(avg - ref[:, None, :], axis=-1).mean(1) / np.linalg.norm(ref, axis=-1)
                e_big = np.linalg.norm(P_big - ref[:, None, :], axis=-1).mean(1) / np.linalg.norm(ref, axis=-1)
                # also top-3 set accuracy
                a3 = (topk_sets(avg, 3) == ref3[:, None, :]).all(-1).mean(1)
                b3 = (topk_sets(P_big, 3) == ref3[:, None, :]).all(-1).mean(1)
                split_rows.append(dict(dataset=ds, model=kind, est=est, mult=mult, k=kk, err_avg_median=np.median(e_avg),
                                       err_single_median=np.median(e_big), ratio_median=np.median(e_avg / np.maximum(e_big, 1e-12)),
                                       acc3_avg=a3.mean(), acc3_single=b3.mean()))

# aggregate certificate over clusters, pooled across models (cluster = model x instance)
for (ds, mult, tag, thr), lst in sorted(clusters.items(), key=lambda t: (t[0][0], t[0][1], t[0][2], t[0][3])):
    cs = np.concatenate([x[0] for x in lst]); cc = np.concatenate([x[1] for x in lst])
    rr = np.concatenate([x[2] for x in lst])
    p, lo, hi = ratio_boot(cc, cs)
    cv, clo, chi = ratio_boot(cs, rr)
    cert_rows.append(dict(dataset=ds, mult=mult, target=tag, thr=thr, coverage=cv, cov_lo=clo, cov_hi=chi,
                          precision=p, prec_lo=lo, prec_hi=hi, n_clusters=len(cs)))
C = pd.DataFrame(cert_rows)
C.to_csv(os.path.join(TAB, f"tabF_cert{suffix}.csv"), index=False)
pd.DataFrame(agree_rows).to_csv(os.path.join(TAB, f"tabF2_agree{suffix}.csv"), index=False)
S = pd.DataFrame(split_rows)
S.to_csv(os.path.join(TAB, f"tabG_split{suffix}.csv"), index=False)
print(C[C.target == "top1"].round(3).to_string())
print(S.groupby(["est", "k"])[["ratio_median", "acc3_avg", "acc3_single"]].mean().round(3))
