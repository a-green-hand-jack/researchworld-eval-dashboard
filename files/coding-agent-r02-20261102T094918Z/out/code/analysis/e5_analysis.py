"""Image-/centre-bootstrap analysis of the real-data experiment (E5 CIFAR-10H, E7 ChaosNLI)."""
import sys; sys.path.insert(0, "/work/analysis")
import numpy as np, pandas as pd
import os
ALPHA = float(os.environ.get("ALPHA", 0.1))
NB = 10
SEED = 0


def load(tag):
    suffix = tag if tag.startswith("_") else ("" if tag == "cifar10h" else "_" + tag)
    return pd.read_csv(f"/work/results/e5_rep{suffix}.csv"), np.load(f"/work/results/e5_img{suffix}.npz")


def boot_stats(img, cfg, meth, score, B=300, seed=SEED):
    """Pooled (all-split) expected coverage per image -> slice-level coverage, worst-gap, with image bootstrap."""
    te = img[f"{cfg}|te_cnt"]
    pool = np.where(te > 0)[0]
    p = img[f"{cfg}|{meth}|{score}"][pool] / te[pool]
    conf, cls = img[f"{cfg}|conf"][pool], img[f"{cfg}|cls"][pool]
    edges = np.quantile(conf, np.linspace(0, 1, NB + 1)[1:-1])
    bconf = np.searchsorted(edges, conf, side="right")
    ncls = cls.max() + 1 if cls.max() > 2 else 3
    slices = {"conf": (bconf, NB), "class": (cls, int(max(cls.max() + 1, 3)))}

    def stat(idx):
        out = {"cov": p[idx].mean()}
        for k, (key, nb) in slices.items():
            cs = np.array([p[idx][key[idx] == b].mean() for b in range(nb) if (key[idx] == b).any()])
            out["G_" + k] = np.abs(cs - (1 - ALPHA)).max()
            out["min_" + k] = cs.min()
        return out
    pt = stat(np.arange(len(pool)))
    rng = np.random.default_rng(seed)
    bs = [stat(rng.integers(0, len(pool), len(pool))) for _ in range(B)]
    res = {}
    for k in pt:
        v = np.array([b[k] for b in bs])
        res[k] = (pt[k], np.quantile(v, 0.025), np.quantile(v, 0.975))
    # per-decile coverage curve (point + bootstrap band) for plotting
    curve = np.array([p[bconf == b].mean() for b in range(NB)])
    cb = np.array([[p[idx][bconf[idx] == b].mean() for b in range(NB)] for idx in (rng.integers(0, len(pool), len(pool)) for _ in range(B))])
    res["curve"] = (curve, np.quantile(cb, 0.025, axis=0), np.quantile(cb, 0.975, axis=0))
    # log-mass (Dir(1)) with centre bootstrap
    k = f"{cfg}|lm|{meth}|{score}"
    if k in img:
        cnt = img[f"{cfg}|lm_cnt"]
        lm = img[k] / np.maximum(cnt, 1)
        v = [lm[rng.integers(0, len(lm), len(lm))].mean() for _ in range(B)]
        res["lm1"] = (lm.mean(), np.quantile(v, 0.025), np.quantile(v, 0.975))
    return res


def table(tag, cfg, combos, B=300):
    rep, img = load(tag)
    rows = []
    for meth, score in combos:
        s = boot_stats(img, cfg, meth, score, B)
        r = rep[(rep["model"] + "_" + rep["mode"] == cfg) & (rep.method == meth) & (rep.score == score)]
        rows.append(dict(method=meth, score=score, cov_split_mean=r["cov"].mean(), cov_sd=r["cov"].std(),
                         null_conf=r.null_worst_conf.mean(), null_class=r.null_worst_class.mean(),
                         **{k: v for k, v in s.items() if k != "curve"}))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "cifar10h"
    cfg = sys.argv[2] if len(sys.argv) > 2 else "resnet56_T"
    sc = ["euclid", "tv", "hellinger", "chi2", "kl"] + [f"aitchison_{d}" for d in ("1e-4", "1e-3", "1e-2", "1e-1")]
    combos = [("split", s) for s in sc] + [("mondrian_conf", s) for s in ("euclid", "chi2", "kl")] + [("mondrian_class", s) for s in ("euclid", "chi2", "kl")]
    df = table(tag, cfg, combos, B=100)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(df[["method", "score", "cov", "G_conf", "G_class", "min_conf", "lm1", "null_conf", "null_class"]].to_string())
