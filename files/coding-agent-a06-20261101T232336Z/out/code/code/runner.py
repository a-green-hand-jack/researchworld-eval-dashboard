"""Generic Monte-Carlo runner: cells -> rows, parallel over cells, results saved as parquet."""
import sys, time, itertools, numpy as np, pandas as pd, multiprocessing as mp
sys.path.insert(0, "/work/code")
from sel import *; from mc import *; from synth import *

_W = {}
def get_world(spec):
    key = tuple(sorted(spec.items()))
    if key not in _W:
        if spec["kind"] == "synth":
            rng = np.random.default_rng(spec.get("seed", 0))
            if spec.get("iid"):
                K = spec["K"]
                dist = spec.get("dist", "normal")
                if dist == "normal": mu = spec["tau"] * rng.standard_normal(K)
                elif dist == "sparse":      # 5% of configs are better by 4*tau, rest identical
                    mu = np.zeros(K); mu[rng.choice(K, max(1, K // 20), replace=False)] = 4 * spec["tau"]; mu -= mu.mean()
                elif dist == "heavy":       # student-t(3) config effects scaled to sd tau
                    mu = rng.standard_t(3, K); mu = spec["tau"] * mu / mu.std()
                elif dist == "bimodal":     # half the configs broken (format failures), half good with small spread
                    mu = np.where(rng.random(K) < 0.5, -3 * spec["tau"], 0.0) + 0.3 * spec["tau"] * rng.standard_normal(K); mu -= mu.mean()
            else:
                mu = make_mu(spec["tau"], rng)
            a = spec.get("a", -0.4)
            acc = acc_from_mu(a, mu)
            Y = draw_items(mu, a, spec["rho"], spec.get("N", 20000), rng)
            _W.clear(); _W[key] = (Y, acc)
        elif spec["kind"] == "real2":
            from realdata import load_pool2
            Y = load_pool2()
            _W.clear(); _W[key] = (Y, None)
        elif spec["kind"] == "real":
            from realdata import load_Y
            Y = load_Y(spec["cache"], spec.get("pool"))
            _W.clear(); _W[key] = (Y, None)
    return _W[key]

def run_cell(args):
    cell, nrep, seed = args
    Y, acc = get_world(cell["world"])
    rng = np.random.default_rng(seed)
    rows = []
    for r in range(nrep):
        if cell["method_set"] == "main":
            out = trial(Y, cell["n"], cell["algo"], cell["kw"], rng, truth_acc=acc, nboot=cell.get("nboot", 100),
                        rho_hold=cell.get("rho_hold", 0.3), wr=cell.get("wr", False))
        elif cell["method_set"] == "rs_extras":
            out = trial_rs_extras(Y, cell["n"], cell["kw"]["B"], rng, truth_acc=acc, wr=cell.get("wr", False))
        elif cell["method_set"] == "naive":
            out = trial_naive(Y, cell["n"], cell["algo"], cell["kw"], rng, truth_acc=acc, wr=cell.get("wr", False))
        else:
            raise ValueError
        for m, v in out.items():
            rows.append(dict(rep=r, method=m, est=v[0], lo=v[1], hi=v[2], truth=v[3]))
    df = pd.DataFrame(rows)
    for k, v in cell.items():
        if k in ("world", "kw"):
            if k == "world":
                for kk, vv in v.items(): df["w_" + kk] = vv
            else:
                for kk, vv in v.items(): df["kw_" + kk] = vv
        else: df[k] = v
    return df

def run_cells(cells, nrep, out, procs=3, seed0=1000):
    t = time.time()
    tasks = [(c, nrep, seed0 + i) for i, c in enumerate(cells)]
    dfs = []
    with mp.Pool(procs) as p:
        for i, d in enumerate(p.imap_unordered(run_cell, tasks)):
            dfs.append(d)
            if i % 10 == 0: print(f"{i+1}/{len(tasks)} cells, {time.time()-t:.0f}s", flush=True)
    pd.concat(dfs).to_parquet(out)
    print("saved", out, f"{time.time()-t:.0f}s")
