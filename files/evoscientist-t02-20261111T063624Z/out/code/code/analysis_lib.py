"""Shared helpers for analysis: loading, censoring-aware summaries, bootstrap CIs."""
import json, os, collections
import numpy as np

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
rng = np.random.default_rng(0)


def load(name):
    rows = []
    seen = set()
    for l in open(os.path.join(RES, name + ".jsonl")):
        r = json.loads(l)
        if r["key"] in seen:  # duplicate (run twice by accident): keep first
            continue
        seen.add(r["key"])
        c = r["cfg"]
        r["tt"] = r["t_train"] if r["t_train"] is not None else c["max_steps"]
        r["tv"] = r["t_val"] if r["t_val"] is not None else c["max_steps"]
        rows.append(r)
    return rows


def group(rows, keyfn):
    g = collections.defaultdict(list)
    for r in rows:
        g[keyfn(r)].append(r)
    return dict(sorted(g.items(), key=lambda kv: kv[0]))


def boot_median_ci(x, n=4000, alpha=0.05):
    x = np.asarray(x, float)
    if len(x) == 0:
        return (np.nan, np.nan, np.nan)
    idx = rng.integers(0, len(x), (n, len(x)))
    meds = np.median(x[idx], axis=1)
    return (float(np.median(x)), float(np.quantile(meds, alpha / 2)), float(np.quantile(meds, 1 - alpha / 2)))


def summarize(rs, field):
    """field in tt, tv, R (=tv/tt), D (=tv-tt). Censored (tv at max_steps) values are lower bounds."""
    if field == "R":
        x = [r["tv"] / r["tt"] for r in rs]
    elif field == "D":
        x = [r["tv"] - r["tt"] for r in rs]
    else:
        x = [r[field] for r in rs]
    which = "train" if field == "tt" else "val"
    flag = float(n_cens(rs, which) * 2 >= len(rs))
    return boot_median_ci(x) + (flag,)


def n_cens(rs, which="val"):
    return sum(r["val_cens"] if which == "val" else r["train_cens"] for r in rs)
