"""Fixed-game, grouped-feature permutation SHAP reliability experiment.
Logical costs do not take credit for cache hits. Not a SHAP package speed benchmark.
"""
import os
for _k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[_k]='1'
from pathlib import Path
import argparse, json, math, time, warnings, hashlib, platform
import numpy as np
import pandas as pd
from scipy.io import arff
from scipy.special import expit
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score, log_loss, accuracy_score
from joblib import Parallel, delayed, dump
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
SEEDS=[11,23,47]; BUDGETS=[1,4,16,64]; R=20; N=30

def load_data(name,n_instances=N,manifest_suffix=''):
    if name=='pima':
        a,_=arff.loadarff(ROOT/'data/pima.arff'); df=pd.DataFrame(a)
        y=(df.pop('class')==b'tested_positive').astype(int).to_numpy()
        for c in ['plas','pres','skin','insu','mass']: df.loc[df[c]==0,c]=np.nan
        cats=[]; groups=np.arange(len(df)); src='OpenML 37 v1'
    elif name=='german':
        names=['status','duration','history','purpose','amount','savings','employment','installment','personal','debtors','residence','property','age','other_installments','housing','credits','job','dependents','telephone','foreign','class']
        df=pd.read_csv(ROOT/'data/german/german.data',sep=r'\s+',names=names)
        y=(df.pop('class')==2).astype(int).to_numpy() # positive = bad credit
        cats=[c for c in df if not pd.api.types.is_numeric_dtype(df[c].dtype)]; groups=np.arange(len(df)); src='UCI Statlog German raw categorical file'
    elif name=='acs':
        from folktables import ACSIncome
        raw=pd.read_pickle(ROOT/'data/acs2018vt.pkl')
        # Match ACSIncome adult_filter; retain household grouping.
        filt=ACSIncome.df_to_pandas(raw)[0]
        selected=raw[(raw.AGEP>16)&(raw.PINCP>100)&(raw.WKHP>0)&(raw.PWGTP>=1)]
        # package adult_filter uses PINCP>100 (not >=100).
        x,y,_=ACSIncome.df_to_numpy(raw)
        assert len(selected)==len(x)
        df=pd.DataFrame(x,columns=ACSIncome.features)
        y=y.astype(int); groups=selected.SERIALNO.astype(str).to_numpy()
        cats=['COW','MAR','OCCP','POBP','RELP','SEX','RAC1P']; src='ACS 2018 1-Year person Vermont, folktables ACSIncome'
    else: raise ValueError(name)
    idx=np.arange(len(y))
    if name=='acs':
        splitter=GroupShuffleSplit(n_splits=1,test_size=.2,random_state=2026)
        tv,te=next(splitter.split(idx,y,groups))
        spl=GroupShuffleSplit(n_splits=1,test_size=.25,random_state=2027)
        tr0,va0=next(spl.split(tv,y[tv],groups[tv])); tr=tv[tr0];va=tv[va0]
    else:
        tv,te=train_test_split(idx,test_size=.2,random_state=2026,stratify=y)
        tr,va=train_test_split(tv,test_size=.25,random_state=2027,stratify=y[tv])
    # Per-feature preprocessing is separable, permitting grouped mask after transform.
    arrays=[];colgroups=[];transforms=[]
    for j,c in enumerate(df):
        raw=df[[c]]
        imp=SimpleImputer(strategy='most_frequent' if c in cats else 'median')
        imp.fit(raw.iloc[tr]); a=imp.transform(raw)
        transform=OneHotEncoder(handle_unknown='ignore',sparse_output=False) if c in cats else StandardScaler()
        transform.fit(a[tr]); z=transform.transform(a)
        arrays.append(z); colgroups.extend([j]*z.shape[1]); transforms.append((imp,transform))
    X=np.concatenate(arrays,axis=1).astype(np.float64)
    rng=np.random.default_rng(9041)
    # one sampled test person per household, so household == instance cluster
    pool=[];seen=set()
    for i in rng.permutation(te):
        if groups[i] not in seen: pool.append(int(i));seen.add(groups[i])
        if len(pool)>=n_instances: break
    bg=np.random.default_rng(9042).choice(tr,size=16,replace=False)
    meta={'dataset':name,'source':src,'n':len(y),'d':len(df.columns),'encoded_d':X.shape[1],
          'features':list(df.columns),'categorical':cats,'train':tr.tolist(),'validation':va.tolist(),'test':te.tolist(),
          'instances':pool,'background':bg.tolist(),'positive_fraction':float(y.mean()),
          'duplicate_raw_rows':int(df.duplicated().sum()),'missing_entries':int(df.isna().sum().sum()),
          'household_disjoint': name=='acs','test_cluster_ids':[str(groups[i]) for i in pool]}
    if len(pool)!=n_instances:
        raise ValueError(f'Requested {n_instances} audit instances but only {len(pool)} eligible clusters')
    (OUT/f'data_{name}{manifest_suffix}.json').write_text(json.dumps(meta,indent=2))
    return X,y,np.array(colgroups),tr,va,te,np.array(pool),bg,meta,transforms

class Game:
    def __init__(self,model,x,bg,colgroups,d):
        self.model=model;self.x=x;self.bg=bg;self.colgroups=colgroups;self.d=d
        self.cache=np.full(1<<d,np.nan); self.actual_rows=0;self.pred_seconds=0.
    def values(self,ids):
        ids=np.asarray(ids,dtype=np.int64)
        todo=np.unique(ids[np.isnan(self.cache[ids])])
        t=time.perf_counter()
        for start in range(0,len(todo),1024):
            chunk=todo[start:start+1024]
            masks=((chunk[:,None]>>self.colgroups)&1).astype(bool)
            hybrid=np.where(masks[:,None,:],self.x[None,None,:],self.bg[None,:,:]).reshape(-1,len(self.x))
            pred=self.model.predict_proba(hybrid)[:,1].reshape(len(chunk),len(self.bg)).mean(axis=1)
            self.cache[chunk]=pred;self.actual_rows+=len(hybrid)
        self.pred_seconds+=time.perf_counter()-t
        return self.cache[ids]

def paths(rng,cycles,d,antithetic=True):
    perm=np.array([rng.permutation(d) for _ in range(cycles)])
    if antithetic: perm=np.stack([perm,perm[:,::-1]],axis=1).reshape(-1,d)
    bits=1<<perm
    ids=np.concatenate([np.zeros((len(perm),1),dtype=np.int64),np.cumsum(bits,axis=1)],axis=1)
    return perm,ids

def contributions(values,perm):
    inc=np.diff(values,axis=1);out=np.zeros_like(inc)
    np.put_along_axis(out,perm,inc,axis=1)
    return out

def sample(game,seed,cycles,antithetic=True):
    perm,ids=paths(np.random.default_rng(seed),cycles,game.d,antithetic)
    return contributions(game.values(ids),perm)

def exact_shapley(v,d):
    ids=np.arange(1<<d);phi=np.zeros(d)
    sizes=np.array([int(s).bit_count() for s in ids])
    for j in range(d):
        s=ids[(ids&(1<<j))==0];k=sizes[s]
        w=np.array([1/(d*math.comb(d-1,int(a))) for a in k])
        phi[j]=np.sum(w*(v[s|(1<<j)]-v[s]))
    return phi

def kernel_estimate(v,d,m,seed):
    """Plain constrained Kernel SHAP, iid kernel-size law, no feature selection."""
    rng=np.random.default_rng(seed); allids=np.arange(1,(1<<d)-1)
    sizes=np.array([int(i).bit_count() for i in allids])
    if m>=len(v):
        ids=allids; w=(d-1)/np.array([math.comb(d,int(s))*s*(d-s) for s in sizes])
    else:
        k=np.arange(1,d); probs=1/(k*(d-k));probs=probs/probs.sum()
        chosen=rng.choice(k,size=max(d,m-2),p=probs)
        ids=np.array([sum(1<<int(j) for j in rng.choice(d,size=s,replace=False)) for s in chosen])
        w=np.ones(len(ids))
    Z=((ids[:,None]>>np.arange(d))&1).astype(float)
    # eliminate final coefficient to enforce efficiency exactly
    delta=v[-1]-v[0];A=Z[:,:-1]-Z[:,-1:];b=v[ids]-v[0]-Z[:,-1]*delta
    beta=np.linalg.lstsq(A*np.sqrt(w[:,None]),b*np.sqrt(w),rcond=1e-10)[0]
    return np.r_[beta,delta-beta.sum()]

def fit_model(name,seed,X,y,tr):
    if name=='lr': model=LogisticRegression(C=1,max_iter=1000,random_state=seed)
    elif name=='rf': model=RandomForestClassifier(n_estimators=40,max_depth=6,min_samples_leaf=4,n_jobs=1,random_state=seed)
    else: model=MLPClassifier(hidden_layer_sizes=(32,16),alpha=.01,max_iter=350,early_stopping=True,validation_fraction=.15,n_iter_no_change=20,random_state=seed)
    t=time.perf_counter()
    with warnings.catch_warnings(record=True) as ws:
        model.fit(X[tr],y[tr])
    return model,time.perf_counter()-t,[str(w.message) for w in ws]

def run_cell(dataset,model_name,seed,n=N,reps=R,refcycles=512,sensitivity=False):
    threadpool_limits(1)
    suffix='_b16' if sensitivity else ''
    path=OUT/f'{dataset}_{model_name}_{seed}{suffix}.npz'
    if path.exists():
        try:
            report=json.loads(path.with_suffix('.json').read_text())
            expected=(n,reps,len(BUDGETS))
            with np.load(path,allow_pickle=False) as saved:
                shape=saved['phi'].shape
                if len(shape)!=4 or shape[:3]!=expected:
                    raise ValueError(f'phi shape {shape}, expected {expected} + (d,)')
                if saved['instances'].shape!=(n,) or not np.array_equal(saved['budgets'],BUDGETS):
                    raise ValueError('stored instances or budgets do not match requested run')
            requested={'n':n,'repetitions':reps,'background':16 if sensitivity else 8}
            for key,value in requested.items():
                if report.get(key)!=value:
                    raise ValueError(f'{key}={report.get(key)!r}, expected {value}')
        except (OSError,ValueError,KeyError) as exc:
            raise ValueError(f'Cannot skip existing cell {path}: {exc}. Existing files left unchanged.') from exc
        return {'skip':str(path)}
    started=time.time();cpu0=time.process_time()
    X,y,cg,tr,va,te,instances,bgids,meta,transforms=load_data(dataset,n_instances=n,manifest_suffix=suffix)
    model,train_secs,warn=fit_model(model_name,seed,X,y,tr)
    bg=X[bgids[:16 if sensitivity else 8]];instances=instances[:n];d=meta['d']
    dump({'model':model,'transforms':transforms,'colgroups':cg,'metadata':meta},OUT/f'model_{dataset}_{model_name}_{seed}{suffix}.joblib',compress=3)
    prob=model.predict_proba(X[te])[:,1]
    metrics={'auc':roc_auc_score(y[te],prob),'log_loss':log_loss(y[te],prob),'accuracy':accuracy_score(y[te],prob>=.5)}
    attrs=[];refs=[];refs2=[];basic=[];kernels=[];counters=[];eff=[]
    for ii,idx in enumerate(instances):
        game=Game(model,X[idx],bg,cg,d)
        if d<=10:
            v=game.values(np.arange(1<<d));ref=exact_shapley(v,d);ref2=ref.copy()
        else:
            a=sample(game,500000+ii*100+seed,refcycles).mean(axis=0)
            b=sample(game,900000+ii*100+seed,refcycles).mean(axis=0)
            ref=(a+b)/2;ref2=np.stack([a,b])
        phis=[];nonanti=[];ks=[]
        for r in range(reps):
            # Stable stream map, independent reference streams; datasets/models share random permutations.
            stream=11000000+seed*100000+ii*1000+r
            c=sample(game,stream,64).reshape(64,2,d).mean(axis=1)
            phis.append(np.array([c[:p].mean(axis=0) for p in BUDGETS]))
            if d<=10:
                # Same interior-row cost: 2P iid one-way paths vs P antithetic pairs.
                nc=sample(game,stream+20000000,128,False)
                nonanti.append(np.array([nc[:2*p].mean(axis=0) for p in BUDGETS]))
                ks.append(np.array([kernel_estimate(v,d,2+2*p*(d-1),stream+30000000+p) for p in BUDGETS]))
        phis=np.array(phis)
        attrs.append(phis);refs.append(ref);refs2.append(ref2)
        if nonanti: basic.append(nonanti);kernels.append(ks)
        residual=float(np.max(np.abs(phis.sum(axis=-1)-(game.values([2**d-1])[0]-game.values([0])[0]))))
        eff.append(residual)
        counters.append({'actual_rows':game.actual_rows,'prediction_seconds':game.pred_seconds,'cached_coalitions':int(np.isfinite(game.cache).sum())})
        print(f'{dataset}/{model_name}/{seed}{suffix}: {ii+1}/{len(instances)} rows={game.actual_rows} eff={residual:.2g}',flush=True)
    np.savez_compressed(path,phi=np.array(attrs),reference=np.array(refs),reference_pools=np.array(refs2),
                        nonantithetic=np.array(basic),kernel=np.array(kernels),instances=instances,budgets=BUDGETS,efficiency=eff)
    report={'dataset':dataset,'model':model_name,'seed':seed,'n':len(instances),'repetitions':reps,'background':len(bg),'reference_cycles_per_pool':refcycles if d>10 else 0,
            'reference_type':'exact_enumeration' if d<=10 else 'two_independent_permutation_pools',
            'train_seconds':train_secs,'metrics':metrics,'warnings':warn,'counters':counters,'wall_seconds':time.time()-started,'cpu_seconds':time.process_time()-cpu0,
            'model_parameters':model.get_params(),'logical_model_rows_per_run':{str(p):len(bg)*(2+2*p*(d-1)) for p in BUDGETS}}
    path.with_suffix('.json').write_text(json.dumps(report,indent=2))
    return report

def main():
    global OUT
    ap=argparse.ArgumentParser();ap.add_argument('--jobs',type=int,default=8);ap.add_argument('--pilot',action='store_true');ap.add_argument('--sensitivity',action='store_true');ap.add_argument('--instances',type=int,default=N);ap.add_argument('--output',type=Path,default=OUT);args=ap.parse_args()
    OUT=args.output.resolve();OUT.mkdir(exist_ok=True,parents=True)
    if args.pilot:
        OUT=OUT/'pilot'; OUT.mkdir(exist_ok=True)
        print(run_cell('pima','lr',11,n=2,reps=3));return
    tasks=[(ds,m,s) for ds in ['pima','acs','german'] for m in ['lr','rf','mlp'] for s in SEEDS]
    if args.sensitivity: tasks=[(ds,m,11) for ds in ['pima','acs'] for m in ['lr','rf','mlp']]
    res=Parallel(n_jobs=args.jobs)(delayed(run_cell)(*t,n=10 if args.sensitivity else args.instances,sensitivity=args.sensitivity) for t in tasks)
    (OUT/('sensitivity_run.json' if args.sensitivity else 'main_run.json')).write_text(json.dumps(res,indent=2))
if __name__=='__main__':main()
