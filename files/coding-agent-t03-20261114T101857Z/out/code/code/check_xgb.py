# sanity: on Pima (d=8, exhaustive KernelSHAP), compare exact enumeration with TreeSHAP for XGB in margin vs probability mode
import numpy as np, shap
from common import *
Xtr,Xte,ytr,yte=split("pima"); m=make_model("xgb",0).fit(Xtr,ytr)
bg=Xtr.values[np.random.RandomState(1).choice(len(Xtr),50,replace=False)]; X=Xte.values[:20]
for name,f,mo in [("margin",lambda A:m.predict(A,output_margin=True),"raw"),("probability",lambda A:m.predict_proba(A)[:,1],"probability")]:
    ex=shap.KernelExplainer(f,bg).shap_values(X,nsamples=1000,silent=True,l1_reg=0)
    tr=shap.TreeExplainer(m,data=bg,feature_perturbation="interventional",model_output=mo).shap_values(X,check_additivity=False)
    print(name,"max|exact-TreeSHAP|",np.abs(ex-tr).max(),"rel",np.linalg.norm(ex-tr)/np.linalg.norm(ex))
