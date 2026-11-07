from pathlib import Path
from io import BytesIO
import zipfile, json
import numpy as np
import pandas as pd
from scipy.io import arff
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/raw'

def load_data(name):
    if name=='german':
        with zipfile.ZipFile(RAW/'german.zip') as z:
            member=next(n for n in z.namelist() if n.endswith('german.data'))
            df=pd.read_csv(BytesIO(z.read(member)),sep=r'\s+',header=None)
        names=['checking','duration','history','purpose','amount','savings','employment','installment_rate','personal_status_sex','debtors','residence','property','age','other_installments','housing','existing_credits','job','dependents','telephone','foreign_worker']
        X=df.iloc[:,:20].copy(); X.columns=names
        cats=[i for i in range(20) if pd.api.types.is_string_dtype(X.iloc[:,i])]
        y=(df.iloc[:,20].to_numpy()==2).astype(int)  # adverse credit class
        source={'version':'UCI Statlog German Credit, raw german.data','target':'bad credit (original label 2)'}
    elif name=='diabetes':
        a,_=arff.loadarff(RAW/'diabetes.arff'); df=pd.DataFrame(a)
        X=df.iloc[:,:-1].copy(); cats=[]
        y=(df.iloc[:,-1].to_numpy()==b'tested_positive').astype(int)
        # Conventional missingness: physiologically impossible zeros, not pregnancies.
        for col in ['plas','pres','skin','insu','mass']:
            if col in X: X.loc[X[col]==0,col]=np.nan
        source={'version':'OpenML data_id=37 version=1','target':'tested_positive','zero_to_missing':['plas','pres','skin','insu','mass']}
    elif name=='acs':
        from folktables import ACSIncome
        with zipfile.ZipFile(RAW/'acs2018_ca.zip') as z:
            member=next(n for n in z.namelist() if n.endswith('.csv'))
            # Keep source row order; source contains records outside ACSIncome filter.
            with z.open(member) as stream:
                df=pd.concat(pd.read_csv(stream,usecols=list(set(ACSIncome.features+['PINCP','PWGTP'])),chunksize=65536,low_memory=True),ignore_index=True)
        arr,y,_=ACSIncome.df_to_numpy(df)
        X=pd.DataFrame(arr,columns=ACSIncome.features,index=ACSIncome._preprocess(df).index)
        y=np.asarray(y,dtype=int)
        cats=[X.columns.get_loc(c) for c in ['COW','SCHL','MAR','OCCP','POBP','RELP','SEX','RAC1P']]
        source={'version':'ACS PUMS 2018 1-year California person CSV; folktables 0.0.12 ACSIncome filter','target':'PINCP > 50000','filter':'AGEP>16, PINCP>100, WKHP>0, PWGTP>=1','survey_weights_used':False,'row_id_semantics':'zero-based source person CSV row after header, retained through ACSIncome filter'}
    else: raise ValueError(name)
    # Category identity is fit on training only by downstream encoders.
    for j in cats: X[X.columns[j]]=X.iloc[:,j].astype(str)
    source.update(n_rows=len(y),n_features=X.shape[1],feature_names=list(X.columns),categorical_indices=cats,positive_rate=float(y.mean()))
    return X,y,cats,source
