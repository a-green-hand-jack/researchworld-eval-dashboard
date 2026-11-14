"""Run the full fixed-seed audit. Results are JSON/CSV, never hand-entered."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[key]='1'
import argparse,json,time,platform,resource
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.linalg import solve
from bt import BT,kendall_distance
from data import load_panels,matched_mt,make,nba_home,ROOT

SEED=20261102
BUDGETS=[0.,.0001,.0005,.001,.002,.005,.01,.02,.05,.1]


def serial(obj):
    if isinstance(obj,np.generic):return obj.item()
    if isinstance(obj,np.ndarray):return obj.tolist()
    raise TypeError(type(obj))


def bootstrap(p,bt,t,c,rng,repeats):
    clusters,ci=np.unique(p.cluster,return_inverse=True)
    gaps=[];leaders=[]
    for rep in range(repeats):
        multiplicity=np.bincount(rng.integers(len(clusters),size=len(clusters)),minlength=len(clusters))
        weights=multiplicity[ci]
        count=np.bincount(p.group,weights=weights,minlength=len(p.X))
        wins=np.bincount(p.group,weights=weights*p.y,minlength=len(p.X))
        tb=bt.fit(count,wins,t)
        gaps.append(float(c@tb));leaders.append(int(np.argmax(tb[:p.m])))
    return np.array(gaps),np.array(leaders)


def random_flips(p,bt,t,c,rng,repeats):
    eligible=np.flatnonzero(p.y!=.5)
    records=[]
    order=t[:p.m].argsort()[::-1]
    for rep in range(repeats):
        perm=rng.permutation(eligible)
        wins=p.wins.copy();prev=0;current=t
        for fraction in BUDGETS:
            k=min(int(np.ceil(fraction*p.n)),len(eligible))
            ids=perm[prev:k]
            wins+=np.bincount(p.group[ids],weights=1-2*p.y[ids],minlength=len(p.X))
            current=bt.fit(wins=wins,start=current)
            records.append(dict(panel=p.name,rep=rep,fraction=fraction,k=k,
                gap=float(c@current),pair_reversed=int(c@current < -1e-9),
                leader_lost=int(np.argmax(current[:p.m])!=order[0]),
                kendall=kendall_distance(t[:p.m],current[:p.m])))
            prev=k
    return records


def run(args):
    start=time.time();out=ROOT/'results';out.mkdir(exist_ok=True)
    summaries=[];random=[];boots=[];adjacent=[];paths={};ablations=[]
    allpanels=load_panels()
    for ix,p in enumerate(allpanels):
        began=time.time();bt=BT(p);t=bt.fit();rank=np.argsort(-t[:p.m],kind='stable');first,second=rank[:2]
        c=bt.contrast(first,second)
        # Independent reproducible streams, unaffected by other experiment sizes.
        rng=np.random.default_rng(np.random.SeedSequence([SEED,ix,0]))
        gaps,leaders=bootstrap(p,bt,t,c,rng,args.bootstrap)
        sd=float(np.std(gaps,ddof=1))
        attacks={
            'static':bt.attack(t,c),
            'adaptive':bt.attack(t,c,adaptive=True),
            'incident':bt.attack(t,c,scope='incident'),
            'delete':bt.attack(t,c,mode='delete'),
            'resolution':bt.attack(t,c,margin=2*sd),
        }
        cert=bt.certificate(t,c)
        direct=bt.direct_bound(t,c)
        incident=np.isin(p.a,[first,second]) | np.isin(p.b,[first,second])
        leader_n=int(np.sum((p.a==first)|(p.b==first)))
        record=dict(panel=p.name,n=p.n,m=p.m,decisive=int(sum(p.y!=.5)),
            clusters=len(np.unique(p.cluster)),leader=p.models[first],runner=p.models[second],
            leader_n=leader_n,pair_support=int(incident.sum()),gap=float(c@t),
            bootstrap_sd=sd,gap_lo=float(np.quantile(gaps,.025)),gap_hi=float(np.quantile(gaps,.975)),
            bootstrap_pair_reverse=float(np.mean(gaps<0)),bootstrap_leader_lost=float(np.mean(leaders!=first)),
            safe_k=cert['safe_k'],safe_incident=bt.certificate(t,c,'incident')['safe_k'],
            lower_k=direct['lower_k'],direct_capacity=direct['capacity'],
            exact=bool(direct['lower_k']==attacks['static']['k']),
            k=attacks['static']['k'],adaptive_k=attacks['adaptive']['k'],
            incident_k=attacks['incident']['k'],delete_k=attacks['delete']['k'],
            resolution_k=attacks['resolution']['k'],predicted_k=attacks['static']['predicted_k'])
        record['global_pct']=100*record['k']/p.n if record['k'] is not None else None
        record['leader_pct']=100*record['k']/leader_n if record['k'] is not None else None
        # Actual touched leader rows distinguish this contextual denominator
        # from the fraction of its records that were actually modified.
        chosen=np.array(attacks['static']['ids'],int)
        record['touched_leader']=int(np.sum((p.a[chosen]==first)|(p.b[chosen]==first)))
        paths[p.name]=dict(ranking=[p.models[i] for i in rank],scores=t.tolist(),
                          attacks=attacks,certificate=cert,direct_bound=direct)
        for rep,(gap,leader) in enumerate(zip(gaps,leaders)):
            boots.append(dict(panel=p.name,rep=rep,gap=gap,leader=p.models[leader]))
        random+=random_flips(p,bt,t,c,np.random.default_rng(np.random.SeedSequence([SEED,ix,1])),args.random)
        for j in range(min(10,p.m)-1):
            cc=bt.contrast(rank[j],rank[j+1]);at=bt.attack(t,cc)
            adjacent.append(dict(panel=p.name,position=j+1,first=p.models[rank[j]],second=p.models[rank[j+1]],
                gap=float(cc@t),k=at['k'],predicted_k=at['predicted_k'],safe_k=bt.certificate(t,cc)['safe_k'],
                **bt.direct_bound(t,cc)))
        # Fixed pair in regularization/tie-policy controls; do not reselect it.
        for ridge in [.1,10.]:
            b=BT(p,ridge);tt=b.fit();aa=b.attack(tt,c)
            ablations.append(dict(panel=p.name,variant=f'ridge-{ridge:g}',leader=p.models[np.argmax(tt[:p.m])],
                gap=float(c@tt),k=aa['k'],predicted_k=aa['predicted_k']))
        if np.any(p.y==.5):
            pp=p.subset(np.flatnonzero(p.y!=.5));b=BT(pp);tt=b.fit();cc=b.contrast(first,second);aa=b.attack(tt,cc)
            ablations.append(dict(panel=p.name,variant='drop-ties',leader=p.models[np.argmax(tt[:p.m])],
                gap=float(cc@tt),k=aa['k'],predicted_k=aa['predicted_k']))
        if p.name.startswith('NBA'):
            pp=nba_home(int(p.name[-4:]));b=BT(pp);tt=b.fit();cc=b.contrast(first,second);aa=b.attack(tt,cc)
            ablations.append(dict(panel=p.name,variant='home-covariate',leader=p.models[np.argmax(tt[:pp.m])],
                gap=float(cc@tt),k=aa['k'],predicted_k=aa['predicted_k'],home_coefficient=float(tt[-1])))
        record['seconds']=time.time()-began;record['fits']=bt.fit_count;record['max_gradient']=bt.max_residual
        summaries.append(record)
        pd.DataFrame(summaries).to_csv(out/'summary.csv',index=False)
        print(json.dumps(record,default=serial),flush=True)
    # Matched-schedule robustness to the randomly chosen human annotator.
    matched=[]
    for rep in range(args.matched):
        h,g=matched_mt(SEED+rep)
        for name,d in [('human',h),('GPT4',g)]:
            p=make('matched',d);b=BT(p);t=b.fit();first=p.models.index('gpt-4');second=p.models.index('claude-v1')
            c=b.contrast(first,second);a=b.attack(t,c)
            matched.append(dict(rep=rep,judge=name,n=p.n,gap=float(c@t),k=a['k']))
    pd.DataFrame(random).to_csv(out/'random.csv',index=False)
    pd.DataFrame(boots).to_csv(out/'bootstrap.csv',index=False)
    pd.DataFrame(adjacent).to_csv(out/'adjacent.csv',index=False)
    pd.DataFrame(ablations).to_csv(out/'ablations.csv',index=False)
    pd.DataFrame(matched).to_csv(out/'matched.csv',index=False)
    (out/'paths.json').write_text(json.dumps(paths,indent=2,default=serial)+'\n')
    meta=dict(seed=SEED,bootstrap_repeats=args.bootstrap,random_repeats=args.random,
        matched_repeats=args.matched,budgets=BUDGETS,seconds=time.time()-start,
        python=platform.python_version(),platform=platform.platform(),
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        blas_threads=1,gpu_used=False)
    (out/'run.json').write_text(json.dumps(meta,indent=2)+'\n');print(meta,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--bootstrap',type=int,default=500)
    parser.add_argument('--random',type=int,default=500);parser.add_argument('--matched',type=int,default=100)
    run(parser.parse_args())
