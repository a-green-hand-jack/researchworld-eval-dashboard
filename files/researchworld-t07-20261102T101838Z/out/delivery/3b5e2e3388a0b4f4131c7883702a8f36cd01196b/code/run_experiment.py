"""Main experiment: for one benchmark and split kind, repeat (split draw, selection draw) and store per-target predictions.
usage: python run_experiment.py BENCH KIND REPS OUT.parquet [--budgets 10,25,50,100,200] [--irt_d 4]"""
import argparse, time, hashlib, json
import numpy as np, pandas as pd
from bpx import data, splits, methods


def seed_of(*a):
    return int(hashlib.sha256("|".join(map(str, a)).encode()).hexdigest()[:8], 16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bench"); ap.add_argument("kind"); ap.add_argument("reps", type=int); ap.add_argument("out")
    ap.add_argument("--budgets", default="10,20,50,100,200"); ap.add_argument("--irt_d", type=int, default=4)
    ap.add_argument("--pipelines", default=""); ap.add_argument("--tfrac", type=float, default=0.25)
    ap.add_argument("--sfrac_sub", type=float, default=0.0, help="subsample this fraction of S each rep (0: default 0.8 for deterministic splits, 1 for random)")
    ap.add_argument("--s_size", type=int, default=0, help="restrict S to this many source models (Q5)")
    ap.add_argument("--inner", action="store_true", help="design-freezing mode: first draw the outer split with the same seed, keep only its S as the whole population")
    ap.add_argument("--no_dedup", action="store_true")
    ap.add_argument("--tag", default="", help="label appended to split_type (ablations)")
    ap.add_argument("--factorial", action="store_true", help="use the selector x estimator grid instead of named pipelines")
    a = ap.parse_args()
    pipes = methods.factorial_grid() if a.factorial else {k: v for k, v in methods.PIPELINES.items() if not a.pipelines or k in a.pipelines.split(",")}
    S, names, info = data.load(a.bench, dedup=not a.no_dedup)
    N = S.shape[1]
    budgets = [int(x) for x in a.budgets.split(",") if int(x) <= N // 4]       # A3: n capped at N/4
    rows, timing = [], []
    t0 = time.time()
    for rep in range(a.reps):
        rng = np.random.default_rng(seed_of(a.bench, a.kind, rep, "split"))
        Sp, nm = S, np.array(names)
        if a.inner:
            o_src, _ = splits.make_split("random" if a.kind == "random" else a.kind, S, names, np.random.default_rng(seed_of(a.bench, "outer", rep)), a.tfrac)
            Sp, nm = S[o_src], nm[o_src]
            gidx = o_src
        else:
            gidx = np.arange(S.shape[0])
        src_i, tgt_i = splits.make_split(a.kind, Sp, list(nm), rng, a.tfrac, fold=rep)
        sub = a.sfrac_sub if a.sfrac_sub > 0 else (1.0 if a.kind in ("random", "group") else 0.8)
        if sub < 1.0:                                  # A2: variability of deterministic splits from S-subsampling
            src_i = np.sort(rng.choice(src_i, int(round(sub * len(src_i))), replace=False))
        if a.s_size:
            src_i = np.sort(rng.choice(src_i, min(a.s_size, len(src_i)), replace=False))
        tm = time.time()
        src = methods.Source(Sp[src_i], irt_d=a.irt_d, seed=rep)
        timing.append(dict(rep=rep, step="fit_source", seconds=time.time() - tm))
        Yfull = Sp[tgt_i].astype(np.float32); true = Yfull.mean(1)   # y_T over ALL N items (A1)
        for n in budgets:
            cache = {}
            for pname, (sname, ename) in pipes.items():
                tm = time.time()
                if sname not in cache:
                    r = np.random.default_rng(seed_of(a.bench, a.kind, rep, n, sname))
                    cache[sname] = methods.SELECTORS[sname](src, n, r)
                idx, wt = cache[sname]
                r = np.random.default_rng(seed_of(a.bench, a.kind, rep, n, pname, "est"))
                pred = methods.ESTIMATORS[ename](src, idx, wt, Yfull[:, idx], r)   # target rows revealed on idx only
                rows.append(pd.DataFrame(dict(benchmark=a.bench, split_type=a.kind + ("_inner" if a.inner else "") + a.tag, s_frac=len(src_i) / S.shape[0],
                                              n_source=len(src_i), n=n, seed=rep, split_id=f"{a.kind}-{rep}", method=pname,
                                              target_model=np.array(names)[gidx[tgt_i]], true=true, pred=pred, n_used=len(idx))))
                timing.append(dict(rep=rep, step=f"{pname}@{n}", seconds=time.time() - tm))
        print(f"HUTIAN_PROGRESS {a.bench} {a.kind} rep {rep+1}/{a.reps} {time.time()-t0:.0f}s", flush=True)
    df = pd.concat(rows, ignore_index=True)
    df.to_parquet(a.out, compression="zstd")
    json.dump(dict(info=info, args=vars(a), budgets=budgets, timing=pd.DataFrame(timing).groupby("step").seconds.sum().to_dict()), open(a.out + ".json", "w"))


if __name__ == "__main__":
    main()
