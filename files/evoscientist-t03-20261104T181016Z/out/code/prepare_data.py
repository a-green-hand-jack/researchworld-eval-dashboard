"""Allowlisted data acquisition and train-only preprocessing; run from workspace root."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[k]='1'
import io, json, hashlib, zipfile, time, platform
from pathlib import Path
import numpy as np
import pandas as pd
import requests
import joblib
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, balanced_accuracy_score, log_loss, brier_score_loss
from folktables import ACSIncome
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
SEEDS=[11,29,47]

def fetch(url, dest):
    p=DATA/dest
    if not p.exists():
        r=requests.get(url,timeout=180); r.raise_for_status(); p.write_bytes(r.content)
        with (ART/'data_access.jsonl').open('a') as f:
            f.write(json.dumps(dict(url=url,status=r.status_code,final_url=r.url,path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(r.content).hexdigest()))+'\n')
    return p

def acquire():
    z=fetch('https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip','german.zip')
    with zipfile.ZipFile(z) as f:
        names=f.namelist(); name=[n for n in names if n.endswith('german.data')][0]
        df=pd.read_csv(io.BytesIO(f.read(name)),sep=r'\s+',header=None)
        desc=[n for n in names if n.endswith('german.doc')]
        if desc: (DATA/'german.doc').write_bytes(f.read(desc[0]))
    gn=['checking_status','duration','credit_history','purpose','amount','savings','employment','installment_rate','personal_status_sex','other_debtors','residence_since','property','age','other_installment_plans','housing','existing_credits','job','dependents','telephone','foreign_worker']
    gcat=[0,2,3,5,6,8,9,11,13,14,16,18,19]
    gx=df.iloc[:,:20].copy(); gx.columns=gn
    gy=(df.iloc[:,20].to_numpy()==2).astype(int)
    # Public fixed-version OpenML record. Retain the downloaded cache in data/openml.
    p=DATA/'pima.csv'
    if not p.exists():
        raw=fetch_openml(data_id=37,as_frame=True,data_home=str(DATA/'openml'),parser='auto')
        pf=raw.frame; pf.to_csv(p,index=False)
        (ART/'pima_openml_metadata.json').write_text(json.dumps(raw.details,indent=2,default=str))
        with (ART/'data_access.jsonl').open('a') as f: f.write(json.dumps(dict(url='https://www.openml.org/d/37',access='sklearn.fetch_openml(data_id=37)',version=raw.details.get('version'),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))+'\n')
    pf=pd.read_csv(p); px=pf.iloc[:,:8].astype(float); py=(pf.iloc[:,8].astype(str)=='tested_positive').astype(int).to_numpy()
    for col in px.columns[[1,2,3,4,5]]: px.loc[px[col]==0,col]=np.nan
    # Direct official file, same source used by folktables ACSDataSource.
    z=fetch('https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/csv_pca.zip','acs2018_ca_person.zip')
    frames=[]
    with zipfile.ZipFile(z) as f:
        for n in f.namelist():
            if n.lower().endswith('.csv'): frames.append(pd.read_csv(f.open(n),low_memory=False))
    acs=pd.concat(frames,ignore_index=True)
    ax,ay,_=ACSIncome.df_to_numpy(acs)
    eligible=len(ay)
    take=np.random.default_rng(20261103).choice(eligible,min(20000,eligible),replace=False)
    ax=pd.DataFrame(ax[take],columns=ACSIncome.features); ay=ay[take].astype(int)
    # Source IDs retained separately to make the record-level design auditable.
    af=ACSIncome._preprocess(acs)
    source=(af['SERIALNO'].astype(str)+'/'+af['SPORDER'].astype(str)).iloc[take].tolist()
    (DATA/'acs_selected_source_ids.json').write_text(json.dumps(source))
    terms=fetch('https://www.census.gov/about/policies/privacy/data_stewardship.html','census_data_stewardship.html')
    return [('german',gx,gy,gcat,dict(source='UCI Statlog German Credit',raw_n=len(gx),positive='bad credit (2)',license='CC BY 4.0')),
            ('acs',ax,ay,[1,3,4,5,6,8,9],dict(source='ACS PUMS 2018 California 1-Year person / folktables0.0.12 ACSIncome',raw_n=len(acs),eligible_n=eligible,positive='PINCP > 50000',license='US Census public-use microdata; not survey-weighted')),
            ('pima',px,py,[],dict(source='OpenML37 version1 diabetes',raw_n=len(px),positive='tested_positive',license='Public (OpenML record)'))]

def prepare():
    metrics=[]; manifest={}
    for ds,x,y,cat,meta in acquire():
        ids=np.arange(len(y)); tr,te=train_test_split(ids,test_size=.2,stratify=y,random_state=20261104)
        selected=np.random.default_rng(20261105).choice(te,72,replace=False)
        bg=np.random.default_rng(20261106).choice(tr,64,replace=False)
        blocks=[]; groups=[]; transforms=[]
        for j in range(x.shape[1]):
            a=x.iloc[:,[j]].copy()
            if j in cat:
                a=a.astype(str); imp=SimpleImputer(strategy='most_frequent'); atr=imp.fit_transform(a.iloc[tr]); enc=OneHotEncoder(handle_unknown='ignore',sparse_output=False,dtype=np.float64); enc.fit(atr); z=enc.transform(imp.transform(a)); unknown=int(np.sum(~a.iloc[te,0].isin(enc.categories_[0])))
            else:
                a=a.astype(float); imp=SimpleImputer(strategy='median'); atr=imp.fit_transform(a.iloc[tr]); enc=StandardScaler().fit(atr); z=enc.transform(imp.transform(a)); unknown=0
            groups.extend([j]*z.shape[1]); blocks.append(z); transforms.append((imp,enc))
            meta.setdefault('unknown_test_categories',{})[str(x.columns[j])]=unknown
        e=np.ascontiguousarray(np.concatenate(blocks,axis=1)); groups=np.array(groups)
        meta.update(n=len(y),d=x.shape[1],encoded_d=e.shape[1],train_n=len(tr),test_n=len(te),class_rate=float(np.mean(y)),duplicate_features=int(x.duplicated().sum()),constant_features=[str(c) for c in x.columns if x[c].nunique(dropna=False)<=1],missing_counts=x.isna().sum().to_dict(),features=list(x.columns),categorical_indices=cat)
        b=dict(dataset=ds,e=e,y=y,groups=groups,train=tr,test=te,selected=selected,background=bg,features=list(x.columns),meta=meta)
        joblib.dump(b,DATA/f'{ds}_bundle.joblib',compress=3)
        x.to_csv(DATA/f'{ds}_features.csv',index=False); np.save(DATA/f'{ds}_labels.npy',y)
        mp=ROOT/'models'; mp.mkdir(exist_ok=True)
        for seed in SEEDS:
            models=dict(lr=LogisticRegression(C=1,max_iter=2000,tol=1e-8,random_state=seed),rf=RandomForestClassifier(n_estimators=80,max_depth=6,max_features='sqrt',random_state=seed,n_jobs=1),hgb=HistGradientBoostingClassifier(max_iter=80,max_leaf_nodes=15,learning_rate=.1,min_samples_leaf=20,l2_regularization=0,early_stopping=False,random_state=seed))
            for name,model in models.items():
                t=time.perf_counter(); cpu=time.process_time(); model.fit(e[tr],y[tr]); sec=time.perf_counter()-t; cp=time.process_time()-cpu
                pro=model.predict_proba(e[te])[:,1]; m=dict(dataset=ds,model=name,seed=seed,n_train=len(tr),n_test=len(te),auc=roc_auc_score(y[te],pro),balanced_accuracy=balanced_accuracy_score(y[te],pro>=.5),log_loss=log_loss(y[te],pro),brier=brier_score_loss(y[te],pro),wall_s=sec,cpu_s=cp,prediction_hash=hashlib.sha256(pro.tobytes()).hexdigest(),n_iter=str(getattr(model,'n_iter_',None)),params=model.get_params())
                joblib.dump(model,mp/f'{ds}_{name}_{seed}.joblib',compress=3); metrics.append(m)
        meta['split_hash']=hashlib.sha256(tr.tobytes()+te.tobytes()).hexdigest(); meta['selected']=selected.tolist(); meta['background']=bg.tolist(); meta['selected_hash']=hashlib.sha256(selected.tobytes()).hexdigest(); manifest[ds]=meta
    (ART/'data_manifest.json').write_text(json.dumps(manifest,indent=2,default=str)); (ART/'model_metrics.json').write_text(json.dumps(metrics,indent=2,default=str))
    pd.DataFrame([{k:v for k,v in m.items() if k!='params'} for m in metrics]).to_csv(ART/'model_metrics.csv',index=False)

if __name__=='__main__': prepare()
