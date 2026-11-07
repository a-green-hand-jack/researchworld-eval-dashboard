"""Run train/validation/test model experiments; writes every model-level loss."""
import argparse,json,pathlib,time
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split,GroupShuffleSplit
from methods import moments,order,predict,losses,factor_covariance
ROOT=pathlib.Path(__file__).resolve().parents[1]

def split_rows(frame,condition,seed):
    ix=np.arange(len(frame));complete=frame.notna().all(axis=1).to_numpy()
    if condition=='provider':
        groups=np.array([s.split('__')[0] if '__' in s else s.split('/')[0] for s in frame.index])
        for offset in range(100):
            rs=seed+offset*1000
            trainval,test=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=rs).split(ix,groups=groups))
            tr,va=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=rs+1).split(trainval,groups=groups[trainval]))
            train,val=trainval[tr],trainval[va]
            if complete[val].sum()>=6 and complete[test].sum()>=6:return train,val[complete[val]],test[complete[test]],rs
        raise ValueError('No adequate group split')
    if condition=='temporal':
        meta=pd.read_csv(ROOT/'data/open_llm_metadata.csv',index_col=0).reindex(frame.index)
        dates=pd.to_datetime(meta['Submission Date'],errors='coerce');valid=np.flatnonzero(dates.notna())
        ordered=valid[np.argsort(dates.iloc[valid].to_numpy(),kind='stable')]
        n=len(ordered);return ordered[:int(.6*n)],ordered[int(.6*n):int(.8*n)],ordered[int(.8*n):],seed
    trainval,test=train_test_split(ix,test_size=.2,random_state=seed,stratify=complete if not complete.all() else None)
    train,val=train_test_split(trainval,test_size=.25,random_state=seed+100,stratify=complete[trainval] if not complete.all() else None)
    return train,val[complete[val]],test[complete[test]],seed

def run(dataset,condition,seeds,out):
    start=time.time();frame=pd.read_csv(ROOT/f'data/{dataset}.csv',index_col=0);x=frame.to_numpy(float);n=x.shape[1]
    ks=[k for k in [0,1,2,4,8,16] if k<n];records=[];designs=[];splits=[]
    for seed in seeds:
        trainix,valix,testix,actual_seed=split_rows(frame,condition,seed)
        assert not (set(trainix)&set(valix) or set(trainix)&set(testix) or set(valix)&set(testix))
        train=x[trainix].copy();val=x[valix];test=x[testix]
        assert np.isfinite(val).all() and np.isfinite(test).all()
        assert len(train)>0 and len(val)>0 and len(test)>0
        if condition.startswith('missing'):
            frac=int(condition.removeprefix('missing'))/100
            train[np.random.default_rng(seed+200).random(train.shape)<frac]=np.nan
        if condition=='dense_history':train=train[np.isfinite(train).all(axis=1)]
        sd=np.maximum(np.nanstd(train,axis=0,ddof=1),1e-4)
        # Tune covariance shrinkage only on validation models, aggregating k.
        tuning=[]
        for alpha in [.05,.2,.5,.8]:
            mu,cov=moments(train,alpha);query=order(cov,'a_opt',max(ks),np.random.default_rng(seed))
            score=np.mean([losses(val,predict(mu,cov,val,query[:k]),query[:k],sd)['mae'].mean() for k in ks if k>0])
            tuning.append((score,alpha))
        alpha=min(tuning)[1];mu,cov=moments(train,alpha)
        fmu,fcov=factor_covariance(train,rank=min(4,n-1))
        # Ridge penalty is independently tuned at the proposed query sets.
        aq=order(cov,'a_opt',max(ks),np.random.default_rng(seed))
        ridge_scores=[]
        for reg in [.001,.01,.1,1.]:
            score=np.mean([losses(val,predict(mu,cov,val,aq[:k],kind='ridge',train=train,ridge=reg),aq[:k],sd)['mae'].mean() for k in ks if k>0])
            ridge_scores.append((score,reg))
        ridge=min(ridge_scores)[1]
        splitinfo=dict(dataset=dataset,condition=condition,seed=seed,actual_split_seed=actual_seed,
                       train_names=frame.index[trainix].tolist(),validation_names=frame.index[valix].tolist(),test_names=frame.index[testix].tolist(),
                       train_used=len(train),alpha=alpha,ridge=ridge,alpha_validation=tuning,ridge_validation=ridge_scores)
        splits.append(splitinfo)
        policies=['a_opt','d_opt','variance','correlation','random']
        for policy in policies:
            for draw in range(8 if policy=='random' else 1):
                q=order(cov,policy,max(ks),np.random.default_rng(seed*100+draw))
                kinds=['covariance','mean','ability','ridge','factor4'] if policy=='a_opt' else ['covariance']
                for kind in kinds:
                    method=policy+'_'+kind
                    for k in ks:
                        if k==0 and (policy!='a_opt' or kind!='mean'):continue
                        if k>0 and kind=='mean':continue
                        selected=q[:k]
                        pp=predict(fmu,fcov,test,selected) if kind=='factor4' else predict(mu,cov,test,selected,kind=kind,train=train,ridge=ridge)
                        err=losses(test,pp,selected,sd)
                        for i,model in enumerate(frame.index[testix]):
                            records.append(dict(dataset=dataset,condition=condition,seed=seed,draw=draw,method=method,k=k,model=model,**{key:float(v[i]) for key,v in err.items()}))
                        designs.append(dict(dataset=dataset,condition=condition,seed=seed,draw=draw,method=method,k=k,queries=[frame.columns[j] for j in selected]))
        pd.DataFrame(records).to_csv(out/'model_losses.csv',index=False)
        (out/'designs.json').write_text(json.dumps(designs,indent=2)+'\n');(out/'splits.json').write_text(json.dumps(splits,indent=2)+'\n')
        print(f'HUTIAN_WAKE: completed {dataset} {condition} seed={seed}, elapsed={time.time()-start:.1f}s',flush=True)
    (out/'timing.json').write_text(json.dumps(dict(dataset=dataset,condition=condition,seeds=seeds,elapsed_seconds=time.time()-start),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--condition',default='random');p.add_argument('--seeds',type=int,default=10);p.add_argument('--out',required=True);a=p.parse_args();out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True)
    run(a.dataset,a.condition,list(range(a.seeds)),out)
