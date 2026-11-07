"""Run the locked finite-snapshot audit; all CSV rows are actual exact refits.
Use OPENBLAS_NUM_THREADS=1 for predictable CPU performance.
"""
from pathlib import Path
import json,time,platform,sys
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import beta
from bt import BT,ranking,metrics
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results';R.mkdir(exist_ok=True)
MAIN=['arena','mt_human_match','mt_gpt4_match','nba2015']
FRACTIONS=[0,.001,.002,.005,.01,.02,.05]
METHODS=['global_if','pair_incident_if','leader_incident_if','offpair_if','direct_pair']

def candidates(b,f,i,j,method,op='delete'):
    inf=b.influence(f,i,j,op)
    incident=(b.a==i)|(b.b==i)|(b.a==j)|(b.b==j)
    if method=='global_if': mask=np.ones(b.n,bool)
    elif method=='pair_incident_if': mask=incident
    elif method=='leader_incident_if':mask=(b.a==i)|(b.b==i)
    elif method=='offpair_if':mask=~incident
    elif method=='direct_pair':mask=((b.a==i)&(b.b==j)&(b.y>.5))|((b.a==j)&(b.b==i)&(b.y<.5))
    else:raise ValueError(method)
    ids=np.flatnonzero(mask&(inf< -1e-14))
    return ids[np.argsort(inf[ids],kind='stable')],inf

def info(b,f,i,j,ids,op='delete'):
    r=b.refit(f,ids,op);base=f.theta[i]-f.theta[j];gap=r.theta[i]-r.theta[j]
    ii=(b.a==i)|(b.b==i);jj=(b.a==j)|(b.b==j);un=ii|jj
    ni=ii.sum();nj=jj.sum();nu=un.sum();ids=np.asarray(ids,dtype=int)
    return dict(k=len(ids),global_fraction=len(ids)/b.n,union_cost=len(ids)/nu,leader_exposure_loss=float(ii[ids].sum()/ni),runner_exposure_loss=float(jj[ids].sum()/nj),union_exposure_loss=float(un[ids].sum()/nu),offpair_count=int((~un[ids]).sum()),base_gap=float(base),gap=float(gap),reversed=int(gap< -1e-9),components=b.components(ids) if op=='delete' else b.components(),gradmax=r.gradmax,**metrics(f.theta[:b.m],r.theta[:b.m]))

def witness(b,f,i,j,method,op='delete',cap=.2):
    ids,inf=candidates(b,f,i,j,method,op);maxk=min(len(ids),int(cap*b.n))
    tried={0:dict(gap=float(f.theta[i]-f.theta[j]),reversed=0)}
    def at(k):
        if k not in tried: tried[k]=info(b,f,i,j,ids[:k],op)
        return tried[k]
    hi=1;last=0;success=None
    while maxk and hi<=maxk:
        if at(hi)['reversed']:success=hi;break
        last=hi
        if hi==maxk:break
        hi=min(2*hi,maxk)
    if success is not None:
        lo=last;hi=success
        # Bracket search yields a witnessed prefix, not a certified minimum (no monotonicity assumed).
        while hi-lo>1:
            mid=(lo+hi)//2
            if at(mid)['reversed']:hi=mid
            else:lo=mid
        k=hi;res=at(k);status='witness'
    else:
        k=maxk;res=at(k) if k else info(b,f,i,j,[],op);status='not_found'
    return dict(status=status,eligible_harmful=len(ids),max_searched=maxk,refits=len(tried)-1,predicted_gap=float(f.theta[i]-f.theta[j]+inf[ids[:k]].sum()),**res),ids[:k]

def run():
    start=time.time();BASE=[];W=[];CUR=[];BOOT=[];scores=[];saved={};datasets={}
    paths=sorted((ROOT/'data'/'processed').glob('*.csv'))
    for path in paths:
        name=path.stem
        if name=='matched_cells':continue
        df=pd.read_csv(path);datasets[name]=df
        home=name.startswith('nba')
        b=BT(df,home=home);f=b.fit();order=ranking(f.theta[:b.m]);saved[name]=(b,f,order)
        i,j=order[:2];inc=(b.a==i)|(b.b==i)|(b.a==j)|(b.b==j)
        row=dict(dataset=name,n=b.n,m=b.m,components=b.components(),ties_or_half=int(np.sum(b.y==.5)),fractional_outcomes=int(np.sum((b.y!=0)&(b.y!=1))),leader=b.names[i],runner=b.names[j],gap=float(f.theta[i]-f.theta[j]),leader_exposure=int(((b.a==i)|(b.b==i)).sum()),runner_exposure=int(((b.a==j)|(b.b==j)).sum()),union_exposure=int(inc.sum()),headtohead=int((((b.a==i)&(b.b==j))|((b.a==j)&(b.b==i))).sum()),home_score=float(f.theta[-1]) if home else None,gradmax=f.gradmax)
        BASE.append(row)
        scores.extend(dict(dataset=name,model=b.names[t],rank=int(k+1),score=float(f.theta[t])) for k,t in enumerate(order))
        print('baseline',name,b.n,b.m,row['leader'],row['runner'],row['gap'],flush=True)
        pairs=list(zip(order[:4],order[1:5]))
        for q,(i,j) in enumerate(pairs):
            for method in METHODS:
                res,ids=witness(b,f,i,j,method)
                W.append(dict(dataset=name,pair_rank=q+1,leader=b.names[i],runner=b.names[j],method=method,operation='delete',**res))
                if name in MAIN and q==0:
                    safe=name+'_'+method
                    np.savez_compressed(R/(safe+'_witness.npz'),selected=ids,theta_base=f.theta,theta_refit=b.refit(f,ids).theta,models=np.array(b.names))
            if q==0 and name in MAIN:
                for method in ['global_if','pair_incident_if']:
                    res,_=witness(b,f,i,j,method,'flip');W.append(dict(dataset=name,pair_rank=1,leader=b.names[i],runner=b.names[j],method=method,operation='flip',**res))
        i,j=order[:2]
        if name in MAIN:
            for op in ['delete','flip']:
                for method in METHODS:
                    if op=='flip' and method not in ['global_if','pair_incident_if']:continue
                    ids,inf=candidates(b,f,i,j,method,op)
                    for frac in FRACTIONS:
                        requested=int(np.floor(frac*b.n)); k=min(len(ids),requested)
                        res=info(b,f,i,j,ids[:k],op)
                        CUR.append(dict(dataset=name,operation=op,method=method,seed=-1,budget_fraction=frac,requested_k=requested,predicted_gap=float(f.theta[i]-f.theta[j]+inf[ids[:k]].sum()),**res))
                for seed in range(100):
                    rng=np.random.default_rng(10000+seed);ids=rng.permutation(b.n)
                    for frac in FRACTIONS:
                        k=int(np.floor(frac*b.n));res=info(b,f,i,j,ids[:k],op)
                        CUR.append(dict(dataset=name,operation=op,method='random',seed=seed,budget_fraction=frac,requested_k=k,predicted_gap=np.nan,**res))
            # Baseline sampling uncertainty is conditional on this originally selected pair.
            clusters,grp=np.unique(df.cluster.astype(str),return_inverse=True)
            for typ in ['row','cluster']:
                if typ=='cluster' and not name.startswith('mt_'):continue
                rng=np.random.default_rng(20261103)
                for seed in range(200):
                    weights=rng.multinomial(b.n,np.ones(b.n)/b.n) if typ=='row' else rng.multinomial(len(clusters),np.ones(len(clusters))/len(clusters))[grp]
                    r=b.fit(weights=weights,start=f.theta)
                    BOOT.append(dict(dataset=name,type=typ,replicate=seed,gap=float(r.theta[i]-r.theta[j]),leader_same=int(np.argmax(r.theta[:b.m])==i)))
        # Flush after each snapshot so partial runs are auditable.
        for rows,file in [(BASE,'baseline'),(scores,'scores'),(W,'witnesses'),(CUR,'curves'),(BOOT,'bootstrap')]:pd.DataFrame(rows).to_csv(R/f'{file}.csv',index=False)
    # Estimator sensitivity, same leader/runner chosen from main lambda=.1 fit.
    ABL=[]
    for name in MAIN:
        old,of,order=saved[name];i,j=order[:2]
        for lam in [.01,.1,1.]:
            for home in ([True,False] if name.startswith('nba') else [False]):
                b=BT(datasets[name],lam=lam,home=home);f=b.fit()
                res,_=witness(b,f,i,j,'global_if')
                ABL.append(dict(dataset=name,lambda_=lam,home=home,target_i=b.names[i],target_j=b.names[j],**res))
    pd.DataFrame(ABL).to_csv(R/'estimator_ablation.csv',index=False)
    # Matched question bootstrap, paired seeds, fixed common target (human baseline leader/runner).
    PAIR=[];hb,hf,ho=saved['mt_human_match'];gb,gf,go=saved['mt_gpt4_match'];i,j=ho[:2]
    assert hb.names==gb.names
    clusters,grp=np.unique(datasets['mt_human_match'].cluster,return_inverse=True)
    assert np.array_equal(datasets['mt_human_match'].cluster,datasets['mt_gpt4_match'].cluster)
    rng=np.random.default_rng(6767)
    for rep in range(200):
        selected_clusters=rng.integers(len(clusters),size=len(clusters));rows=np.concatenate([np.flatnonzero(grp==k) for k in selected_clusters])
        for name in ['mt_human_match','mt_gpt4_match']:
            # Physically repeat sampled cells: deletions act on sampled cell copies, not fractional weights.
            df=datasets[name].iloc[rows].reset_index(drop=True);b=BT(df);f=b.fit();gap=f.theta[i]-f.theta[j]
            if gap<=0:
                res=dict(k=0,global_fraction=0.,status='already_reversed',gap=gap)
            else:res,_=witness(b,f,i,j,'global_if',cap=.2)
            PAIR.append(dict(dataset=name,replicate=rep,target_i=b.names[i],target_j=b.names[j],base_gap=gap,**res))
    pd.DataFrame(PAIR).to_csv(R/'paired_cluster.csv',index=False)
    meta=dict(elapsed_seconds=time.time()-start,python=sys.version,platform=platform.platform(),numpy=np.__version__,pandas=pd.__version__,seed_random='10000..10099',seed_bootstrap=20261103,seed_paired=6767,lambda_=0.1,fractions=FRACTIONS,main=MAIN,threshold_cap=.2,definition='verified sufficient prefix witness, not a global minimum')
    (R/'run_metadata.json').write_text(json.dumps(meta,indent=2))
    print('DONE',meta,flush=True)
if __name__=='__main__':run()
