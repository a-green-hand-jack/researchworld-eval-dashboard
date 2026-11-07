"""Do conclusions change?  Compare tuned system A with (i) an untuned default and (ii) a tuned system with a small budget.
Works on synthetic worlds or the real cache.  -> results/<name>.parquet  (one row per trial x method)"""
import sys, time, numpy as np, pandas as pd, multiprocessing as mp
sys.path.insert(0, "/work/code")
from sel import *; from mc import *; from synth import *

def one(args):
    spec, nrep, seed = args
    if spec["world"]["kind"] == "synth":
        w = spec["world"]; rng = np.random.default_rng(w["seed"])
        mu = make_mu(w["tau"], rng); a = -0.4; acc = acc_from_mu(a, mu); Y = draw_items(mu, a, w["rho"], 20000, rng)
    else:
        from realdata import load_Y
        Y = load_Y(spec["world"]["cache"]); acc = None
        if spec["world"].get("cols") is not None: Y = Y[:, spec["world"]["cols"]]
    rng = np.random.default_rng(seed); rows = []
    for r in range(nrep):
        out = trial_compare(Y, spec["n"], rng, spec["algoA"], spec["kwA"], spec.get("algoB"), spec.get("kwB"), truth_acc=acc,
                            nboot=spec.get("nboot", 60), wr=spec.get("wr", False))
        for m, (g, se, G) in out.items():
            rows.append(dict(rep=r, method=m, gap=g, se=se, true_gap=G))
    df = pd.DataFrame(rows)
    for k, v in spec.items():
        if k == "world":
            for kk, vv in v.items():
                if kk != "cols": df["w_" + kk] = vv
        elif k in ("kwA", "kwB"): df[k] = str(v)
        else: df[k] = str(v) if v is None else v
    return df

def run(specs, nrep, out, procs=3):
    t = time.time(); dfs = []
    with mp.Pool(procs) as p:
        for i, d in enumerate(p.imap_unordered(one, [(s, nrep, 5000 + i) for i, s in enumerate(specs)])):
            dfs.append(d)
            if i % 5 == 0: print(i + 1, len(specs), f"{time.time()-t:.0f}s", flush=True)
    pd.concat(dfs).to_parquet(out); print("saved", out)

if __name__ == "__main__":
    which, procs, nrep = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    specs = []
    if which == "synth":
        for tau in (0.0, 0.05, 0.1, 0.2):
            for n in (100, 200, 400):
                for algoA, kwA in [("rs", dict(B=72)), ("mipro", dict(B=40)), ("ca", {})]:
                    for algoB, kwB in [(None, None), ("rs", dict(B=4))]:
                        specs.append(dict(world=dict(kind="synth", tau=tau, rho=0.8, seed=11), n=n, algoA=algoA, kwA=kwA, algoB=algoB, kwB=kwB))
        run(specs, nrep, "/work/results/conclusions_synth.parquet", procs)
    if which == "real":
        cache = "/work/cache/q15"
        for n in (100, 200, 400):
            for algoA, kwA in [("rs", dict(B=72)), ("mipro", dict(B=40)), ("ca", {})]:
                for algoB, kwB in [(None, None), ("rs", dict(B=4))]:
                    specs.append(dict(world=dict(kind="real", cache=cache), n=n, algoA=algoA, kwA=kwA, algoB=algoB, kwB=kwB, wr=True))
        run(specs, nrep, "/work/results/conclusions_real.parquet", procs)
