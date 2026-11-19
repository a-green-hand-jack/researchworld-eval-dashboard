"""E8: the cost of honest reporting -- sweep the fraction of the benchmark used for selection under split reporting.

python code/exp_split.py --tag Qwen2.5-0.5B-Instruct_fp32 --out results/split_0.5B.json
"""
import argparse, json, math, sys
import numpy as np
sys.path.insert(0, "code")
import sel
from common import load_matrix, pmap, to_py

ap = argparse.ArgumentParser(); ap.add_argument("--tag", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--R", type=int, default=2000); ap.add_argument("--nproc", type=int, default=4)
a = ap.parse_args()
Y, meta = load_matrix(a.tag); K, N = Y.shape; mu = Y.mean(1)
FR = (0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9)


def job(args):
    n, seed = args
    rng = np.random.default_rng(seed)
    acc = {f: dict(rep=[], truth=[], lo=[], hi=[]) for f in FR}; full = dict(rep=[], truth=[])
    for _ in range(a.R):
        S = rng.integers(0, N, n); Ys = Y[:, S]
        k = sel.opt_exh(Ys, rng); full["rep"].append(Ys[k].mean()); full["truth"].append(mu[k])
        for f in FR:
            n1 = int(round(f * n)); n2 = n - n1
            k1 = sel.opt_exh(Ys[:, :n1], rng); p = Ys[k1, n1:].mean(); lo, hi = sel.wilson(p, n2)
            acc[f]["rep"].append(p); acc[f]["truth"].append(mu[k1]); acc[f]["lo"].append(lo); acc[f]["hi"].append(hi)
    res = dict(n=n, oracle=float(mu.max()), full=dict(truth=float(np.mean(full["truth"])), bias=float(np.mean(np.array(full["rep"]) - np.array(full["truth"]))),
                                                       rmse=float(np.sqrt(np.mean((np.array(full["rep"]) - np.array(full["truth"])) ** 2)))), split={})
    for f in FR:
        r = {k: np.array(v) for k, v in acc[f].items()}
        res["split"][f] = dict(truth=float(r["truth"].mean()), bias=float((r["rep"] - r["truth"]).mean()),
                               rmse=float(np.sqrt(np.mean((r["rep"] - r["truth"]) ** 2))), width=float((r["hi"] - r["lo"]).mean()),
                               cov=float(((r["lo"] <= r["truth"]) & (r["truth"] <= r["hi"])).mean()))
    return res


out = dict(tag=a.tag, K=K, N=N, rows=pmap(job, [(n, 11 + n) for n in (100, 200, 400, 800)], a.nproc))
json.dump(to_py(out), open(a.out, "w"))
for r in out["rows"]:
    print(r["n"], "full", r["full"], {f: (round(v["truth"], 4), round(v["rmse"], 4), round(v["width"], 3), round(v["cov"], 2)) for f, v in r["split"].items()})
