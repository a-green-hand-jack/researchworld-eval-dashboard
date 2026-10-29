"""Run the main experiment grid. Usage: run_exp.py --tag TAG --benchmarks a,b --protocols random,top,org --seeds 0-29
--budgets 10,25,50,100,200 --jobs 38. One pickle per (benchmark, protocol, seed) job is written to results/raw/TAG/."""
import os, sys, argparse, pickle, time
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1"); os.environ.setdefault("MKL_NUM_THREADS", "1")
import numpy as np
from joblib import Parallel, delayed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data, bp

OUT = "/work/results/raw"


def make_split(Y, orgs, protocol, seed):
    m = len(Y)
    rng = np.random.default_rng(10_000 + seed)
    acc = Y.mean(1)
    if protocol == "random":
        perm = rng.permutation(m); nt = int(round(0.3 * m))
        return np.sort(perm[nt:]), np.sort(perm[:nt])
    if protocol.startswith("top"):  # extrapolation: strongest 25% (or top10 / top50) of models are targets
        frac = {"top": 0.25, "top10": 0.10, "top50": 0.50}[protocol]
        order = np.argsort(acc, kind="stable"); nt = int(round(frac * m))
        return np.sort(order[:-nt]), np.sort(order[-nt:])
    if protocol == "bottom":  # extrapolation downwards: weakest 25% of models are targets
        order = np.argsort(acc, kind="stable"); nt = int(round(0.25 * m))
        return np.sort(order[nt:]), np.sort(order[:nt])
    if protocol == "org":  # whole organisations held out (~25-35% of models)
        uo = sorted(set(orgs)); rng.shuffle(uo)
        T = []
        for o in uo:
            T += [i for i in range(m) if orgs[i] == o]
            if len(T) >= 0.25 * m:
                break
        T = np.array(sorted(T)); S = np.setdiff1d(np.arange(m), T)
        return S, T
    raise ValueError(protocol)


def job(bench, protocol, seed, budgets, ds, tag, auto, designs, max_sources=0):
    path = f"{OUT}/{tag}/{bench}__{protocol}__{seed}.pkl"
    if os.path.exists(path):
        return path
    t0 = time.time()
    Y, orgs = data.load(bench)
    S, T = make_split(Y, orgs, protocol, seed)
    if max_sources and max_sources < len(S):  # source-set size ablation: random subset of the source models
        S = np.sort(np.random.default_rng(555_000 + seed).choice(S, max_sources, replace=False))
    rows = bp.evaluate_split(Y, S, T, budgets, seed, ds=ds, auto=auto, designs=designs)
    for r in rows:
        r.update(bench=bench, protocol=protocol, seed=seed, nS=len(S), nT=len(T))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pickle.dump(rows, open(path + ".tmp", "wb")); os.rename(path + ".tmp", path)
    print(f"done {bench} {protocol} {seed} {time.time()-t0:.0f}s", flush=True)
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True); ap.add_argument("--benchmarks", default=",".join(data.ALL))
    ap.add_argument("--protocols", default="random,top,org"); ap.add_argument("--seeds", default="0-29")
    ap.add_argument("--budgets", default="10,25,50,100,200"); ap.add_argument("--ds", default="2,4,8")
    ap.add_argument("--jobs", type=int, default=38); ap.add_argument("--auto", action="store_true"); ap.add_argument("--max_sources", type=int, default=0); ap.add_argument("--designs", default="rand,strat,pps0.5,pps1.0,anchor,dopt")
    a = ap.parse_args()
    designs = tuple(a.designs.split(','))
    s0, s1 = map(int, a.seeds.split("-")); seeds = range(s0, s1 + 1)
    budgets = [int(x) for x in a.budgets.split(",")]; ds = tuple(int(x) for x in a.ds.split(","))
    jobs = []
    for b in a.benchmarks.split(","):
        for p in a.protocols.split(","):
            if p == "org" and b not in data.OPENLLM:
                continue
            for s in seeds:
                jobs.append((b, p, s))
    # big benchmarks first for load balancing
    size = {b: data.load(b)[0].size for b in a.benchmarks.split(",")}
    jobs.sort(key=lambda j: -size[j[0]])
    Parallel(n_jobs=a.jobs, verbose=0)(delayed(job)(b, p, s, budgets, ds, a.tag, a.auto, designs, a.max_sources) for b, p, s in jobs)
