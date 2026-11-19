"""Run the full CPU-only, score-space audit. See README.md for interpretation."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import platform
import resource
import time
from pathlib import Path
import numpy as np
import pandas as pd
from .attacks import (RULES, TOL, aggregate, caps, min_support, min_mass_one,
                      thresholds, all_subsets, support_witness)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
SEED = 20261102
DATASETS = ["helm", "oll", "oll_raw", "oll_all_entries"]

def load(name):
    frame = pd.read_csv(ROOT / f"data/processed/{name}.csv", index_col=0)
    meta = json.loads((ROOT / f"data/processed/{name}_metadata.json").read_text())
    return frame, meta

def common_mask(x):
    return np.logical_and.reduce([aggregate(x, r) < aggregate(x, r).max()-TOL for r in RULES])

def run_support():
    results = []
    for dataset in DATASETS:
        frame, _ = load(dataset); x = frame.values; n, d = x.shape
        common = common_mask(x)
        rank = pd.Series(x.mean(axis=1)).rank(ascending=False, method="min").values
        for cap in ["perfect", "observed"]:
            for rho in [.1, .25, .5, .75, 1.]:
                u = caps(x, cap, rho)
                for margin in [0., 1e-6]:
                    for rule in RULES:
                        tau = thresholds(x, rule, margin)
                        k = min_support(x, u, tau, rule)
                        results.append(pd.DataFrame(dict(dataset=dataset, model=frame.index, rule=rule,
                            cap=cap, rho=rho, margin=margin, k=k, d=d, tau=tau,
                            baseline=aggregate(x, rule), common=common, mean_rank=rank)))
        print(f"support {dataset}: {n} x {d}, {common.sum()} common challengers", flush=True)
    result = pd.concat(results, ignore_index=True)
    result.to_csv(OUT / "support.csv", index=False, float_format="%.15g")
    return result

def run_mass():
    results = []
    for dataset in ["helm", "oll", "oll_raw"]:
        frame, _ = load(dataset); x = frame.values
        common = common_mask(x)
        for cap in ["perfect", "observed"]:
            u = caps(x, cap, 1.)
            for rule in RULES:
                tau = thresholds(x, rule)
                mass = [min_mass_one(a, b, t, rule) for a, b, t in zip(x, u, tau)]
                results.append(pd.DataFrame(dict(dataset=dataset, model=frame.index, cap=cap, rule=rule,
                                                 mass=mass, common=common)))
        print(f"mass {dataset}", flush=True)
    result = pd.concat(results, ignore_index=True)
    result.to_csv(OUT / "mass.csv", index=False, float_format="%.15g")
    return result

def first_hit(scores, tau, d):
    ok = scores >= tau-TOL
    k = ok.argmax(axis=-1)
    k[~ok.any(axis=-1)] = d+1
    return k

def run_baselines():
    rng = np.random.default_rng(SEED)
    records = []
    for dataset in ["helm", "oll"]:
        frame, _ = load(dataset); x = frame.values; n, d = x.shape
        common = common_mask(x)
        threshold_cache = {r: thresholds(x, r) for r in RULES}
        for cap in ["perfect", "observed"]:
          for rho in [.5, 1.]:
            u = caps(x, cap, rho)
            for i in np.flatnonzero(common):
                weak = np.argsort(x[i], kind="stable")
                ym = np.tile(x[i], (d+1, 1))
                for k in range(1, d+1):
                    ym[k, weak[:k]] = u[i, weak[:k]]
                if d <= 6:
                    masks = all_subsets(d)
                    ys = np.where(masks, u[i], x[i])
                else:
                    orders = np.argsort(rng.random((256, d)), axis=1)
                    positions = np.argsort(orders, axis=1)
                    masks = positions[:, None, :] < np.arange(d+1)[None, :, None]
                    ys = np.where(masks, u[i], x[i])
                for rule in RULES:
                    t = threshold_cache[rule][i]
                    wk = int(first_hit(aggregate(ym, rule)[None], t, d)[0])
                    score = aggregate(ys, rule)
                    if d <= 6:
                        pk = np.array([(score[masks.sum(axis=1) == k] >= t-TOL).mean() for k in range(d+1)])
                        rk = float((1-pk[:-1]).sum()) if pk[-1] else float(d+1)
                        rk_se = 0.
                        rp = float(pk[int(np.ceil(.1*d))])
                    else:
                        hits = first_hit(score, t, d)
                        rk = float(hits.mean())
                        rk_se = float(hits.std(ddof=1)/np.sqrt(len(hits)))
                        rp = float((score[:, int(np.ceil(.1*d))] >= t-TOL).mean())
                    records.append(dict(dataset=dataset, model=frame.index[i], cap=cap, rho=rho, rule=rule,
                                        weak_k=wk, random_mean_k=rk, random_success_at_10pct=rp,
                                        random_mean_k_se=rk_se, d=d, random_draws=0 if d <= 6 else 256))
        print(f"baselines {dataset}", flush=True)
    result = pd.DataFrame(records)
    result.to_csv(OUT / "baselines.csv", index=False, float_format="%.15g")

def run_task_bootstrap(b=300):
    rng = np.random.default_rng(SEED+1)
    rows = []
    for dataset in ["helm", "oll"]:
        frame, _ = load(dataset); x = frame.values; n, d = x.shape
        common = common_mask(x)
        for rep in range(b):
            cols = rng.integers(d, size=d)
            z = x[:, cols]
            for cap in ["perfect", "observed"]:
                u = caps(z, cap, 1.)
                km = min_support(z, u, thresholds(z, "mean"), "mean")[common]
                kd = min_support(z, u, thresholds(z, "median"), "median")[common]
                rows.append(dict(dataset=dataset, cap=cap, rep=rep, mean_delta_fraction=float((kd-km).mean()/d),
                             median_cheaper=float((kd<km).mean()), mean_cheaper=float((km<kd).mean()),
                             mean_k_fraction=float(km.mean()/d), median_k_fraction=float(kd.mean()/d)))
        print(f"task bootstrap {dataset}, B={b}", flush=True)
    pd.DataFrame(rows).to_csv(OUT / "task_bootstrap.csv", index=False, float_format="%.15g")

def run_witnesses(support):
    records = []
    for dataset in ["helm", "oll"]:
        frame, _ = load(dataset); x = frame.values
        rows = support.query("dataset == @dataset and cap == 'perfect' and rho == 1 and margin == 0 and common")
        p = rows.pivot(index="model", columns="rule", values="k")
        delta = p['median']-p['mean']
        candidates = [delta.idxmin(), delta.idxmax()]
        for mid in dict.fromkeys(candidates):
            i = frame.index.get_loc(mid)
            for rule in ["mean", "median"]:
                t = thresholds(x, rule)[i]
                sel = support_witness(x[i], np.ones(x.shape[1]), t, rule)
                y = x[i].copy(); y[sel] = 1.
                records.append(dict(dataset=dataset, model=mid, rule=rule, baseline=float(aggregate(x[i],rule)),
                    rival_threshold=float(t), after=float(aggregate(y,rule)), k=len(sel),
                    tasks=frame.columns[sel].tolist(), before_scores=x[i,sel].tolist(), after_scores=y[sel].tolist()))
    (OUT / "witnesses.json").write_text(json.dumps(records, indent=2)+"\n")
    # Audit every computed endpoint witness on the two primary snapshots.
    audited = 0
    for dataset in ["helm", "oll"]:
        frame, _ = load(dataset); x = frame.values
        for cap in ["perfect", "observed"]:
            for rho in [.25, .5, 1.]:
                u = caps(x, cap, rho)
                for rule in RULES:
                    t = thresholds(x, rule)
                    for i in range(len(x)):
                        support_witness(x[i], u[i], t[i], rule)
                        audited += 1
    (OUT / "witness_audit.json").write_text(json.dumps(dict(checked_cases=audited),indent=2)+"\n")

def run_weighting():
    frame, meta = load("helm"); x=frame.values
    w = np.array([meta["n_eval_by_subject"][c][0] for c in frame.columns])
    rows=[]
    for cap in ["perfect", "observed"]:
        for rho in [.25, .5, 1.]:
            for name, weights in [("macro", None), ("micro", w)]:
                t = thresholds(x, "mean", weights=weights)
                k = min_support(x, caps(x, cap, rho), t, "mean", weights=weights)
                rows.append(pd.DataFrame(dict(model=frame.index, cap=cap,rho=rho, weighting=name,k=k,
                                              baseline=aggregate(x,"mean",weights=weights))))
    pd.concat(rows).to_csv(OUT/"weighting.csv",index=False,float_format="%.15g")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--task-bootstrap", type=int, default=300)
    ap.add_argument("--skip-witness-audit", action="store_true")
    args=ap.parse_args(); started=dt.datetime.now(dt.timezone.utc).isoformat(); start=time.perf_counter(); c0=time.process_time()
    OUT.mkdir(exist_ok=True)
    support=run_support(); run_mass(); run_baselines(); run_task_bootstrap(args.task_bootstrap)
    run_weighting()
    if not args.skip_witness_audit:
        run_witnesses(support)
    usage=resource.getrusage(resource.RUSAGE_SELF)
    runtime=dict(started_utc=started, finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(), seed=SEED,
                 task_bootstrap=args.task_bootstrap, wall_seconds=time.perf_counter()-start,
                 process_cpu_seconds=time.process_time()-c0, peak_rss_kib=usage.ru_maxrss,
                 platform=platform.platform(), python=platform.python_version())
    (OUT/"runtime.json").write_text(json.dumps(runtime,indent=2)+"\n")
    print(json.dumps(runtime,indent=2))

if __name__ == "__main__":
    main()
