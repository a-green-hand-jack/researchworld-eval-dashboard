"""Experiment B: conformal sets from probability vectors.  Sources: 'synth' (exact conditional coverage) and 'cifar'."""
import argparse, json, os, time
import numpy as np, pandas as pd
from scipy.special import softmax, log_softmax
from .classif import split_sets, mondrian_sets
from .metrics_b import size_strat, class_cov, SIZE_BINS

METHODS = ["lac", "aps", "raps", "mondrian_lac"]


def synth_pool(rng, N, K, beta, tau, noise):
    """True label probabilities p ~ Dir(beta*1); classifier p_hat = softmax(tau*log p + noise*eps)."""
    p = rng.dirichlet(np.full(K, beta), size=N)
    ph = softmax(tau * np.log(np.maximum(p, 1e-300)) + noise * rng.standard_normal((N, K)), axis=1)
    cum = p.cumsum(1); y = (rng.uniform(size=(N, 1)) > cum).sum(1).clip(0, K - 1)
    return ph, y, p


def cifar_pool(T=1.0, seed_path="/hutian/repo/results/cifar_logits.npz"):
    d = np.load(seed_path)
    L = np.vstack([d["logits_ho"], d["logits_te"]]); y = np.r_[d["y_ho"], d["y_te"]]
    return softmax(L / T, axis=1), y, None


def run_rep(P, y, pt, seed, n_cal, alpha, n_sub=(200, 1000, 5000), methods=METHODS):
    rng = np.random.default_rng(seed)
    N, K = P.shape
    perm = rng.permutation(N); ci, ti = perm[:n_cal], perm[n_cal:]
    Pc, yc, Pt, yt = P[ci], y[ci], P[ti], y[ti]
    rows = []
    for m in methods:
        if m == "mondrian_lac":
            C = mondrian_sets(Pc, yc, Pt, alpha); q = np.nan
        else:
            C, q = split_sets(Pc, yc, Pt, m, alpha, rng)
        cover = C[np.arange(len(yt)), yt]; size = C.sum(1)
        ex = (C * pt[ti]).sum(1) if pt is not None else None
        ssc, sscs = size_strat(cover, size)
        cc = class_cov(cover, yt, K)
        row = dict(method=m, seed=seed, q=q, n_cal=n_cal, cov=cover.mean(), size=size.mean(), empty=(size == 0).mean(),
                   ssc_full=ssc, cc_gap_mean=np.nanmean(np.abs(cc - (1 - alpha))), cc_gap_max=np.nanmax(np.abs(cc - (1 - alpha))),
                   **{f"ssc_bin{i}": c for i, c in enumerate(sscs)})
        if pt is not None:   # exact conditional coverage
            row["cov_exact"] = ex.mean()
            ssc_ex, sscs_ex = [], []
            for lo, hi in SIZE_BINS:
                mk = (size >= lo) & (size <= hi)
                sscs_ex.append(ex[mk].mean() if mk.any() else np.nan)
            row["ssc_exact"] = np.nanmin(sscs_ex)
            row["cond_dev_exact"] = np.abs(ex - (1 - alpha)).mean()
            # top-label-confidence strata of the *true* p (hardness): worst-decile exact coverage
            h = pt[ti].max(1); dec = np.quantile(h, np.linspace(0, 1, 11)); b = np.clip(np.searchsorted(dec, h, side="right") - 1, 0, 9)
            row["hard_decile_min_exact"] = min(ex[b == j].mean() for j in range(10))
        for ns in n_sub:   # what a finite test set would show for SSC
            sub = rng.choice(len(yt), min(ns, len(yt)), replace=False)
            row[f"ssc_est_{ns}"] = size_strat(cover[sub], size[sub])[0]
            # cells with >= 30 points in the subsample only; target = same cells on the full test (exact if known)
            ref = ex if pt is not None else cover
            est_c, tgt_c = [], []
            for lo_, hi_ in SIZE_BINS:
                ms_ = (size[sub] >= lo_) & (size[sub] <= hi_)
                if ms_.sum() >= 30:
                    est_c.append(cover[sub][ms_].mean()); tgt_c.append(ref[(size >= lo_) & (size <= hi_)].mean())
            row[f"ssc30_est_{ns}"] = min(est_c) if est_c else np.nan
            row[f"ssc30_tgt_{ns}"] = min(tgt_c) if tgt_c else np.nan
            row[f"ssc30_ncell_{ns}"] = len(est_c)
            row[f"cov_est_{ns}"] = cover[sub].mean()
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--seed0", type=int, default=0); ap.add_argument("--out", required=True); ap.add_argument("--tag", default="")
    a = ap.parse_args(); cfg = json.loads(a.config)
    src = cfg.pop("source"); n_cal = cfg.pop("n_cal", 1000); alpha = cfg.pop("alpha", 0.1)
    if src == "cifar":
        P, y, pt = cifar_pool(cfg.get("T", 1.0)); fixed = True
    else:
        fixed = False
    rows = []
    for i in range(a.reps):
        if not fixed:   # fresh pool every replication: population-level inference over data draws
            P, y, pt = synth_pool(np.random.default_rng(10_000 + a.seed0 + i), cfg.get("N", 20000), cfg.get("K", 10),
                                  cfg.get("beta", 0.3), cfg.get("tau", 1.0), cfg.get("noise", 0.0))
        t0 = time.time()
        rs = run_rep(P, y, pt, a.seed0 + i, n_cal, alpha)
        for r in rs: r.update(config=a.tag, source=src, **cfg)
        rows += rs
        if i % 10 == 0: print(f"rep {i} {time.time()-t0:.1f}s", flush=True)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    pd.DataFrame(rows).to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
