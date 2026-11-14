"""Define and run all simulation experiments.  Usage: python run_experiments.py E1 [E2 ...] [--jobs 36] [--quick]

Outputs results/<EXP>_reps.csv.gz (one row per population x replicate x estimator) and results/<EXP>_graphs.csv.
Every configuration derives all randomness from (cfg['seed'], population index); seeds are listed in the output.
"""
import argparse
import itertools
import os
import sys
import time
from multiprocessing import Pool

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import pandas as pd  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate.runner import run_config  # noqa: E402

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(RES, exist_ok=True)
BERN = dict(kind="bernoulli", p=0.5)
NP, NR = 4, 150


def G(kind, n=8000, d=10, **kw):
    if kind in ("stanford3", "egofb"):
        return dict(kind=kind, **kw)
    return dict(kind=kind, n=n, d=d, **kw)


def exp_E1():
    """Variance law (correctly specified linear exposure response)."""
    out = []
    # (a) sample-size scaling, d=10, with / without community-correlated baseline
    for kind, n, cs in itertools.product(["er", "ba", "ws", "sbm"], [1000, 2000, 4000, 8000, 16000, 32000], [0.0, 1.0]):
        out.append(dict(tag="nscale", graph=G(kind, n, 10), spec=dict(comm_sd=cs), design=BERN, ests=["dm", "lin_frac", "lin_both"]))
    # (b) degree scaling at n=8000
    for kind, d, cs in itertools.product(["er", "ba", "ws"], [4, 8, 16, 32, 64], [0.0, 1.0]):
        out.append(dict(tag="dscale", graph=G(kind, 8000, d), spec=dict(comm_sd=cs), design=BERN, ests=["dm", "lin_frac", "lin_both"]))
    # (c) treatment probability
    for p, cs in itertools.product([0.05, 0.1, 0.2, 0.3, 0.5], [0.0, 1.0]):
        out.append(dict(tag="pscale", graph=G("er", 8000, 10), spec=dict(comm_sd=cs), design=dict(kind="bernoulli", p=p), ests=["dm", "lin_frac"]))
    # (d) real graphs
    for kind, p, cs in itertools.product(["stanford3", "egofb"], [0.1, 0.3, 0.5], [0.0, 1.0]):
        out.append(dict(tag="real", graph=G(kind), spec=dict(comm_sd=cs), design=dict(kind="bernoulli", p=p), ests=["dm", "lin_frac", "lin_both"]))
    return out


def exp_E2():
    """Bias floor under nonlinear exposure response, Bernoulli design."""
    out = []
    for kind, d, s, p in itertools.product(["er", "ba"], [10, 40], [0, 2, 4, 8, 16], [0.1, 0.25, 0.5, 0.75]):
        out.append(dict(tag="grid", graph=G(kind, 8000, d), spec=dict(s=s), design=dict(kind="bernoulli", p=p),
                        ests=["dm", "lin_frac", "oracle_h"]))
    for kind, s, p in itertools.product(["stanford3", "egofb"], [0, 4, 8, 16], [0.1, 0.5]):
        out.append(dict(tag="real", graph=G(kind), spec=dict(s=s), design=dict(kind="bernoulli", p=p), ests=["dm", "lin_frac", "oracle_h"]))
    for n in [1000, 2000, 4000, 8000, 16000, 32000, 64000]:
        out.append(dict(tag="nfloor", graph=G("er", n, 10), spec=dict(s=8), design=BERN, ests=["lin_frac", "oracle_h"]))
    return out


def exp_E3():
    """Design x estimator under nonlinear response."""
    out = []
    ests = ["dm", "lin_frac", "quad_frac", "spline", "oracle_h", "hajek", "gbm"]
    graphs = [("sbm10", G("sbm", 8000, 20, mix=0.1, K=100)), ("sbm30", G("sbm", 8000, 20, mix=0.3, K=100)),
              ("er", G("er", 8000, 20, K=100)), ("ba", G("ba", 8000, 20, K=100)), ("ws", G("ws", 8000, 20, K=100)),
              ("egofb", G("egofb", K=40)), ("stanford3", G("stanford3", K=100))]
    designs = [dict(kind="bernoulli", p=0.5), dict(kind="cluster", p=0.5), dict(kind="rsat", p=0.5)]
    for gi, ((nm, g), des, s) in enumerate(itertools.product(graphs, designs, [0, 4, 8])):
        # graphs are shared across designs and s (gseed) so the Louvain partition is computed once; gbm only for s=4 (cost)
        out.append(dict(tag="main_" + nm, graph=g, gseed=3000 + [x[0] for x in graphs].index(nm), spec=dict(s=s), design=des,
                        ests=[e for e in ests if e != "gbm" or s == 4], n_pops=3, n_reps=100))
    # sample-size sweep with fixed cluster size (~80 units)
    for n, des in itertools.product([2000, 8000, 32000], designs):
        out.append(dict(tag="nsweep", graph=G("sbm", n, 20, mix=0.1, K=max(n // 80, 10)), spec=dict(s=4), design=des,
                        ests=["lin_frac", "spline", "oracle_h"]))
    # noise sweep
    for sg, des in itertools.product([0.5, 2.0, 4.0], designs):
        out.append(dict(tag="noise", graph=G("sbm", 8000, 20, mix=0.1, K=100), spec=dict(s=4, sigma=sg), design=des,
                        ests=["lin_frac", "spline", "oracle_h"]))
    return out


def exp_E5():
    """Mechanism mismatch: count channel, two-hop spillovers, corrupted graph."""
    out = []
    for kind, d in itertools.product(["er", "ba", "ws"], [10, 30]):
        out.append(dict(tag="count", graph=G(kind, 8000, d), spec=dict(channel="count"), design=BERN,
                        ests=["dm", "lin_frac", "lin_count", "lin_both"]))
    out.append(dict(tag="count", graph=G("stanford3"), spec=dict(channel="count"), design=BERN, ests=["dm", "lin_frac", "lin_count", "lin_both"]))
    out.append(dict(tag="count", graph=G("egofb"), spec=dict(channel="count"), design=BERN, ests=["dm", "lin_frac", "lin_count", "lin_both"]))
    for kind, om, des in itertools.product(["er", "sbm", "ws"], [0, 0.25, 0.5, 0.75], [BERN, dict(kind="cluster", p=0.5)]):
        out.append(dict(tag="twohop", graph=G(kind, 4000, 10, K=50, mix=0.1), spec=dict(channel="twohop", omega=om),
                        design=des, ests=["dm", "lin_frac", "two_hop"]))
    for kind, q, s in itertools.product(["er", "ba", "sbm"], [0, 0.1, 0.25, 0.5], [0, 4]):
        out.append(dict(tag="edgedrop", graph=G(kind, 8000, 20), spec=dict(s=s), design=BERN, edge_drop=q,
                        ests=["dm", "lin_frac", "oracle_h"]))
    return out


def exp_E6():
    """Confidence-interval coverage: HC1 vs 2-hop network-HAC."""
    out = []
    graphs = [("er", G("er", 4000, 10, K=60)), ("sbm", G("sbm", 4000, 10, K=60, mix=0.1)), ("egofb", G("egofb", K=40))]
    for (nm, g), des, s in itertools.product(graphs, [BERN, dict(kind="cluster", p=0.5)], [0, 4]):
        out.append(dict(tag="cov_" + nm, graph=g, spec=dict(s=s), design=des, hac=True, ests=["lin_frac", "oracle_h"], n_reps=200))
    return out


def exp_E7():
    """Diagnostic for E1 on real graphs: does the variance law fail because baseline outcomes depend on network position?"""
    out = []
    for g, dc, cs in itertools.product([G("stanford3"), G("egofb"), G("ba", 8000, 20), G("er", 8000, 20)], [0.0, 0.5, 1.0], [0.0]):
        out.append(dict(tag="degdiag", graph=g, spec=dict(deg_coef=dc, comm_sd=cs), design=BERN, ests=["lin_frac", "lin_both"]))
    return out


EXPS = dict(E1=exp_E1, E2=exp_E2, E3=exp_E3, E5=exp_E5, E6=exp_E6, E7=exp_E7)


def _work(cfg):
    try:
        df, gs = run_config(cfg)
        return cfg["cid"], df, gs, None
    except Exception as e:  # noqa
        import traceback
        return cfg["cid"], None, None, traceback.format_exc()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exps", nargs="+")
    ap.add_argument("--jobs", type=int, default=36)
    ap.add_argument("--drop-last", type=int, default=0, help="drop the last N configs of each experiment (used to skip the n=64000 point)")
    ap.add_argument("--quick", action="store_true", help="tiny smoke test (2 pops x 10 reps, first 3 configs)")
    a = ap.parse_args()
    for ex in a.exps:
        cfgs = EXPS[ex]()
        meta = []
        for i, c in enumerate(cfgs):
            c.update(exp=ex, cid=i, seed=1000 * (list(EXPS).index(ex) + 1) + i)
            c.setdefault("n_pops", NP)
            c.setdefault("n_reps", NR)
            if a.quick:
                c.update(n_pops=2, n_reps=10)
        if a.drop_last:
            cfgs = cfgs[:-a.drop_last]
        if a.quick:
            cfgs = cfgs[:3]
        t0 = time.time()
        dfs, gss, errs = [], [], []
        with Pool(a.jobs) as pool:
            for k, (cid, df, gs, err) in enumerate(pool.imap_unordered(_work, cfgs)):
                if err:
                    errs.append((cid, err))
                    print("ERR", ex, cid, err[-400:], flush=True)
                else:
                    dfs.append(df)
                    gss += gs
                if k % 10 == 0:
                    print(f"{ex} {k + 1}/{len(cfgs)} {time.time() - t0:.0f}s", flush=True)
        cfg_tab = pd.DataFrame([dict(cid=c["cid"], tag=c["tag"], seed=c["seed"], graph=str(c["graph"]), spec=str(c.get("spec", {})),
                                     design=str(c.get("design", {})), edge_drop=c.get("edge_drop", 0.0), n_pops=c["n_pops"],
                                     n_reps=c["n_reps"]) for c in cfgs])
        sfx = "_quick" if a.quick else ""
        pd.concat(dfs).to_csv(os.path.join(RES, f"{ex}_reps{sfx}.csv.gz"), index=False)
        pd.DataFrame(gss).to_csv(os.path.join(RES, f"{ex}_graphs{sfx}.csv"), index=False)
        cfg_tab.to_csv(os.path.join(RES, f"{ex}_configs{sfx}.csv"), index=False)
        print(f"{ex} done in {time.time() - t0:.0f}s, errors={len(errs)}", flush=True)


if __name__ == "__main__":
    main()
