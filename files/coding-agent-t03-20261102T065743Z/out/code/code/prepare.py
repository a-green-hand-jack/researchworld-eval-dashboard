"""Deterministic data preparation and one frozen model per dataset/model cell."""
from common import *
import pandas as pd, json,joblib,time,resource
from scipy.io import arff
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score,accuracy_score,log_loss
from threadpoolctl import threadpool_limits

def get_data(name):
 if name=='german':
  df=pd.read_csv(ROOT/'data/raw/german.data',sep=r'\s+',header=None)
  names=['status','duration','history','purpose','amount','savings','employment','installment','personal','debtors','residence','property','age','other_installment','housing','credits','job','dependents','telephone','foreign']
  y=(df.pop(20)==2).to_numpy().astype(int)
  cats=[0,2,3,5,6,8,9,11,13,14,16,18,19]
  for j in cats:df[j]=pd.Categorical(df[j]).codes
  return df.to_numpy(float),y,names,cats
 if name=='pima':
  raw,_=arff.loadarff(ROOT/'data/raw/diabetes.arff');df=pd.DataFrame(raw)
  y=(df.pop('class')==b'tested_positive').to_numpy().astype(int)
  X=df.to_numpy(float,copy=True);X[:,[1,2,3,4,5]]=np.where(X[:,[1,2,3,4,5]]==0,np.nan,X[:,[1,2,3,4,5]])
  return X,y,list(df.columns),[]
 if name=='acs':
  from folktables import ACSIncome
  df=pd.read_pickle(ROOT/'data/raw/acs_ca2018.pkl')
  X,y,_=ACSIncome.df_to_numpy(df)
  return X.astype(float),y.astype(int),ACSIncome.features,[1,2,3,4,5,6,8,9]

def main():
 infos=[]
 for di,name in enumerate(DATASETS):
  X,y,names,cats=get_data(name);allids=np.arange(len(y))
  train,test=train_test_split(allids,test_size=.25,stratify=y,random_state=SEED)
  if len(train)>20000:train,_=train_test_split(train,train_size=20000,stratify=y[train],random_state=SEED+1)
  imp=SimpleImputer(strategy='median');xt=imp.fit_transform(X[train]);xe=imp.transform(X[test])
  rng=np.random.default_rng(seed_for(di,1));bgids=rng.choice(len(train),BG_SIZE,replace=False);caseids=rng.choice(len(test),N_CASES,replace=False)
  # nested larger background for sensitivity; main B16 is prefix.
  rest=np.setdiff1d(np.arange(len(train)),bgids);bg64=np.r_[bgids,rng.choice(rest,64-BG_SIZE,replace=False)]
  joblib.dump(dict(Xtrain=xt,ytrain=y[train],Xtest=xe,ytest=y[test],names=names,cats=cats,background=xt[bgids],background64=xt[bg64],cases=xe[caseids],caseids=test[caseids],trainids=train,testids=test,bgids=train[bgids]),ROOT/f'data/{name}.joblib')
  for mi,modelname in enumerate(MODELS):
   t=time.perf_counter();cpu=time.process_time()
   if modelname=='logistic':
    nums=[j for j in range(X.shape[1]) if j not in cats]
    transforms=[]
    if nums:transforms.append(('numeric',StandardScaler(),nums))
    if cats:transforms.append(('categorical',OneHotEncoder(handle_unknown='ignore',sparse_output=False),cats))
    pre=ColumnTransformer(transforms)
    enc=pre.fit_transform(xt)
    model=LogisticRegression(C=1,max_iter=2000,random_state=SEED)
    model.fit(enc,y[train]);pred=model.predict_proba(pre.transform(xe))[:,1]
    # Featurewise contribution matrix to the fitted logit, including category lookup.
    def contributions(arr):
     out=np.zeros((len(arr),X.shape[1]));offset=0
     if nums:
      v=pre.named_transformers_['numeric'].transform(arr[:,nums]);out[:,nums]=v*model.coef_[0,:len(nums)];offset=len(nums)
     if cats:
      encobj=pre.named_transformers_['categorical'];v=encobj.transform(arr[:,cats]);start=0
      for j,cat in zip(cats,encobj.categories_):
       n=len(cat);out[:,j]=v[:,start:start+n]@model.coef_[0,offset+start:offset+start+n];start+=n
     return out
    artifact=dict(model=model,pre=pre,kind=modelname,background_contrib=contributions(xt[bgids]),background64_contrib=contributions(xt[bg64]),case_contrib=contributions(xe[caseids]),intercept=float(model.intercept_[0]))
   else:
    model=RandomForestClassifier(n_estimators=64,max_depth=6,min_samples_leaf=5,n_jobs=1,random_state=SEED) if modelname=='forest' else HistGradientBoostingClassifier(max_iter=80,max_leaf_nodes=15,l2_regularization=1.0,random_state=SEED)
    model.fit(xt,y[train]);pred=model.predict_proba(xe)[:,1];artifact=dict(model=model,kind=modelname)
   joblib.dump(artifact,ROOT/f'data/{name}_{modelname}.joblib')
   infos.append(dict(dataset=name,model=modelname,n_total=len(y),n_train=len(train),n_test=len(test),d=X.shape[1],positive_rate=float(y.mean()),auc=roc_auc_score(y[test],pred),accuracy=accuracy_score(y[test],pred>=.5),logloss=log_loss(y[test],pred),train_seconds=time.perf_counter()-t,train_cpu_seconds=time.process_time()-cpu))
   print(infos[-1],flush=True)
 (ROOT/'results/models.json').write_text(json.dumps(infos,indent=2))
if __name__=='__main__':
 with threadpool_limits(limits=1):main()
