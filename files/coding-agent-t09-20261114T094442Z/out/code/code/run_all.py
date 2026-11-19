import sys; sys.path.insert(0,'/work/code')
from sim import *
import itertools
S=dict(sbm=dict(kind='sbm',n=5000,blocks=50,deg=20,rho=0.1),ba=dict(kind='ba',n=5000,m=8),ws=dict(kind='ws',n=5000,deg=20),
       stanford=dict(kind='stanford'),egofb=dict(kind='egofb'))
MODELS=['linfrac','lincount','quad','sigmoid','inter']
R=300; NH=60; sd=[0]
def C(**k):
    sd[0]+=1; d=dict(model='sigmoid',design='bern',p=0.5,gam=1.,R=R,nhgb=NH,seed=sd[0]); d.update(k); return d
exp={}
exp['E1']=[C(graph=S[g],model=m,design=d) for g in S for m in MODELS for d in ['bern','cluster']]
exp['E2']=[C(graph=S['sbm'],model=m,design=d,gam=g) for m in ['linfrac','sigmoid'] for d in ['bern','cluster'] for g in [0,0.5,1,2,4]]
exp['E3']=[C(graph=dict(kind='ws',n=5000,deg=k),model=m) for m in ['linfrac','lincount','sigmoid','quad'] for k in [4,8,16,32,64,128]]
exp['E4']=[C(graph=S['sbm'],model=m,design=d,p=p) for m in ['quad','sigmoid'] for d in ['bern','cluster'] for p in [0.05,0.1,0.25,0.5,0.75]]
exp['E5']=[C(graph=dict(kind='sbm',n=5000,blocks=50,deg=20,rho=r),model=m,design='cluster') for m in ['quad','sigmoid'] for r in [0.02,0.05,0.1,0.2,0.4,0.7,1.0]]
exp['E6']=[C(graph=dict(kind='ws',n=n,deg=20),model=m,nhgb=0) for m in ['linfrac','sigmoid'] for n in [1000,2000,5000,10000,20000,40000]]
exp['E7']=[C(graph=S['sbm'],model=m,sigma=s,nhgb=0) for m in ['linfrac','sigmoid'] for s in [0.25,1,4]]
if __name__=='__main__':
    for k in sys.argv[1:]: main(exp[k],f'/work/results/{k}.json')
