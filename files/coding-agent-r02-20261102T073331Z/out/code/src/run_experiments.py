"""Run all declared experiments. No external datasets, training services, or GPU."""
import argparse, json, os, platform, time, resource
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import qmc, binom
from core import METHODS, SCENARIOS, generate, scores, center, Calibrator

ROOT = Path(__file__).resolve().parents[1]

def volume(calibrator, scenario, seed, power=14):
    """Randomized Sobol integration, jointly over query covariates and set points.

    V2: uniform triangle, V1: equal mixture of uniform open edges. Only K=3.
    Query groups have the test distribution. Each seed gets a new scramble.
    """
    u = qmc.Sobol(6, scramble=True, seed=seed).random_base2(power)
    x = 2*u[:,0]-1
    pg = .65 if scenario == 'shift' else .25
    g = (u[:,1] < pg).astype(int)
    m = center(x, 3)
    e = -np.log(np.maximum(u[:,2:5], np.finfo(float).tiny))
    interior = e/e.sum(axis=1, keepdims=True)
    edge = np.zeros_like(interior)
    dropped = np.minimum((3*u[:,5]).astype(int),2)
    for j in range(3):
        ix = dropped==j
        others = [t for t in range(3) if t!=j]
        edge[ix, others[0]] = u[ix,2]
        edge[ix, others[1]] = 1-u[ix,2]
    a = calibrator.contains(m,interior,g)
    b = calibrator.contains(m,edge,g)
    return {name:(a[name].mean(), b[name].mean()) for name in METHODS}

def one(job):
    scenario, k, rep, ncal, ntest, pilot_n, power, base_seed = job
    sid = list(SCENARIOS).index(scenario)
    seeds = np.random.SeedSequence([base_seed,sid,k,rep]).spawn(4)
    pilot = generate(np.random.default_rng(seeds[0]),pilot_n,k,scenario)
    cal = generate(np.random.default_rng(seeds[1]),ncal,k,scenario)
    pg = .65 if scenario=='shift' else .25
    test = generate(np.random.default_rng(seeds[2]),ntest,k,scenario,pg)
    c = Calibrator.fit(pilot,cal,pg_test=pg,scenario=scenario)
    member = c.contains(test['m'],test['y'],test['g'])
    vol = volume(c,scenario,int(seeds[3].generate_state(1)[0]),power) if k==3 else {}
    out = []
    for method in METHODS:
        hit = member[method]
        row = dict(scenario=scenario,k=k,rep=rep,method=method,coverage=hit.mean(),
                   g0=hit[test['g']==0].mean(),g1=hit[test['g']==1].mean(),
                   boundary=hit[test['zero']].mean() if test['zero'].any() else np.nan,
                   interior=hit[~test['zero']].mean(),
                   n_boundary=int(test['zero'].sum()),n_g1=int(test['g'].sum()),
                   clr_infinite=float(np.isinf(c.thresholds['CLR'])),
                   n_cal_g0_zero=int(((cal['g']==0)&cal['zero']).sum()),
                   hgz_g0_zero_infinite=float(np.isinf(c.thresholds['H-GZ'][0,1])),
                   v2=vol.get(method,(np.nan,np.nan))[0],
                   v1=vol.get(method,(np.nan,np.nan))[1])
        out.append(row)
    return out

def boundary_sweep(seed, repeats=4000):
    rng = np.random.default_rng(seed)
    out=[]
    for n in [99,499,1999]:
        k = int(np.ceil((n+1)*.9))
        for p in [0.,.02,.05,.07,.08,.09,.095,.10,.105,.11,.12,.13,.15,.18,.2]:
            # Actual score arrays, not just binomial counts. F_cont = Exp(1).
            block = 100
            rates=[]; cov=[]; marginal_numer=0; marginal_denom=0
            for start in range(0,repeats,block):
                b = min(block,repeats-start)
                s = rng.exponential(size=(b,n))
                s[rng.random((b,n))<p] = np.inf
                q = np.partition(s,k-1,axis=1)[:,k-1]
                rates.extend(np.isinf(q))
                # Conditional coverage has closed form given q, reducing test noise.
                cp = np.where(np.isinf(q),1.,(1-p)*(-np.expm1(-q)))
                cov.extend(cp)
            rate=np.mean(rates); coverage=np.mean(cov)
            out.append(dict(n=n,p=p,repeats=repeats,collapse=rate,
                collapse_se=np.std(rates,ddof=1)/np.sqrt(repeats),
                collapse_exact=binom.sf(n-k,n,p),coverage=coverage,
                coverage_se=np.std(cov,ddof=1)/np.sqrt(repeats),
                coverage_exact=k/(n+1)+(1-k/(n+1))*binom.sf(n+1-k,n+1,p)))
    return pd.DataFrame(out)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reps',type=int,default=100)
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--seed',type=int,default=20261102)
    parser.add_argument('--ncal',type=int,default=499)
    parser.add_argument('--ntest',type=int,default=2000)
    parser.add_argument('--pilot',type=int,default=1000)
    parser.add_argument('--volume-power',type=int,default=14)
    parser.add_argument('--out',type=Path,default=ROOT/'results')
    args=parser.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter()
    from concurrent.futures import ProcessPoolExecutor
    jobs=[(sc,k,r,args.ncal,args.ntest,args.pilot,args.volume_power,args.seed)
          for sc in SCENARIOS for k in [3,8,20] for r in range(args.reps)]
    records=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i,rows in enumerate(pool.map(one,jobs,chunksize=4)):
            records.extend(rows)
            if (i+1)%100==0: print(f'{i+1}/{len(jobs)} cells; {time.perf_counter()-start:.1f}s',flush=True)
    pd.DataFrame(records).to_csv(args.out/'runs.csv',index=False)
    boundary_sweep(args.seed+1).to_csv(args.out/'boundary_sweep.csv',index=False)
    meta=vars(args).copy();meta['out']=str(meta['out'])
    meta.update(elapsed_seconds=time.perf_counter()-start,python=platform.python_version(),
        platform=platform.platform(),cpu=platform.processor(),logical_cpus=os.cpu_count(),
        maxrss_parent_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        maxrss_child_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        main_cells=len(jobs),independent_repetitions=args.reps,
        note='No GPU. Max RSS is per-process peak, not simultaneous aggregate.')
    (args.out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps(meta,indent=2))

if __name__=='__main__': main()
