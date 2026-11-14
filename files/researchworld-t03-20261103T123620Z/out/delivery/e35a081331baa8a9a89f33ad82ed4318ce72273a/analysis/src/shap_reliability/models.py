import time
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,OrdinalEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score,accuracy_score,log_loss
from .data import load_data

def prepare(name,model_name,seed=20261103,background_size=32,n_instances=60,training_cap=20000):
    X,y,cats,source=load_data(name)
    idx=np.arange(len(y)); train,test=train_test_split(idx,test_size=.2,stratify=y,random_state=seed)
    if len(train)>training_cap:
        train,_=train_test_split(train,train_size=training_cap,stratify=y[train],random_state=seed+1)
    rng=np.random.default_rng(seed+2)
    bgidx=rng.choice(train,min(background_size,len(train)),replace=False)
    explainidx=rng.choice(test,min(n_instances,len(test)),replace=False)
    # One transformer per raw feature preserves a simple and auditable group map.
    transforms=[]
    for j in range(X.shape[1]):
        if j in cats:
            encoder=(OneHotEncoder(handle_unknown='ignore',sparse_output=False,dtype=np.float32) if model_name=='logistic' else OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1,dtype=np.float32))
            trans=Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',encoder)])
        else:
            trans=Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())])
        transforms.append((f'f{j}',trans,[j]))
    prep=ColumnTransformer(transforms,sparse_threshold=0)
    begin=time.perf_counter(); cpu=time.process_time()
    Xt=prep.fit_transform(X.iloc[train]).astype(np.float32)
    if model_name=='logistic': model=LogisticRegression(C=1,max_iter=2000,random_state=seed)
    elif model_name=='forest': model=RandomForestClassifier(n_estimators=100,min_samples_leaf=5,max_features=.8,n_jobs=1,random_state=seed)
    elif model_name=='histboost': model=HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,l2_regularization=1,early_stopping=False,random_state=seed)
    else: raise ValueError(model_name)
    model.fit(Xt,y[train]); train_wall=time.perf_counter()-begin; train_cpu=time.process_time()-cpu
    Xtest=prep.transform(X.iloc[test]).astype(np.float32); pred=model.predict_proba(Xtest)[:,1]
    groups=[np.arange(prep.output_indices_[f'f{j}'].start,prep.output_indices_[f'f{j}'].stop) for j in range(X.shape[1])]
    info=dict(source,model=model_name,model_seed=seed,split_seed=seed,background_seed=seed+2,n_train=len(train),n_test=len(test),training_cap=training_cap,train_ids=train.tolist(),test_ids=test.tolist(),explain_ids=explainidx.tolist(),source_explain_ids=X.index.to_numpy()[explainidx].tolist(),background_ids=bgidx.tolist(),source_background_ids=X.index.to_numpy()[bgidx].tolist(),background_size=len(bgidx),transformed_features=Xt.shape[1],train_wall_seconds=train_wall,train_cpu_seconds=train_cpu,roc_auc=float(roc_auc_score(y[test],pred)),accuracy=float(accuracy_score(y[test],pred>=.5)),log_loss=float(log_loss(y[test],pred)),group_columns=[g.tolist() for g in groups],preprocessing='train-only per-feature median+scale; categorical one-hot for logistic, ordinal codes for trees')
    return dict(model=model,preprocessor=prep,background=prep.transform(X.iloc[bgidx]).astype(np.float32),instances=prep.transform(X.iloc[explainidx]).astype(np.float32),groups=groups,info=info)
