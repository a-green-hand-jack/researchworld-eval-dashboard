"""Ridge Bradley--Terry, exact Newton refits on sufficient edge statistics."""
from dataclasses import dataclass
import numpy as np
from scipy.special import expit
from scipy.linalg import solve
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

@dataclass
class Fit:
    theta: np.ndarray
    hessian: np.ndarray
    objective: float
    gradmax: float
    iterations: int

class BT:
    def __init__(self,df,lam=.1,home=False):
        self.df=df.reset_index(drop=True);self.lam=lam
        self.names=sorted(set(df.a)|set(df.b));self.m=len(self.names);self.n=len(df)
        idx={s:i for i,s in enumerate(self.names)}
        self.a=df.a.map(idx).to_numpy();self.b=df.b.map(idx).to_numpy();self.y=df.y.to_numpy(float)
        self.home=home;self.p=self.m+int(home)
        hh=df.home.to_numpy() if home else np.zeros(self.n)
        keys=np.column_stack([self.a,self.b,hh])
        self.edges,self.group=np.unique(keys,axis=0,return_inverse=True)
        self.X=np.zeros((len(self.edges),self.p))
        self.X[np.arange(len(self.edges)),self.edges[:,0].astype(int)]=1
        self.X[np.arange(len(self.edges)),self.edges[:,1].astype(int)]=-1
        if home:self.X[:,-1]=self.edges[:,2]
        self.C,self.S=self.stats()
    def stats(self,weights=None,y=None):
        w=np.ones(self.n) if weights is None else np.asarray(weights)
        y=self.y if y is None else y
        return np.bincount(self.group,weights=w,minlength=len(self.X)),np.bincount(self.group,weights=w*y,minlength=len(self.X))
    def objective(self,t,C,S):
        z=self.X@t
        return np.sum(C*np.logaddexp(0,z)-S*z)+.5*self.lam*(t@t)
    def derivatives(self,t,C=None,S=None):
        C=self.C if C is None else C;S=self.S if S is None else S
        prob=expit(self.X@t)
        g=self.X.T@(C*prob-S)+self.lam*t
        H=self.X.T@((C*prob*(1-prob))[:,None]*self.X)+self.lam*np.eye(self.p)
        return g,H
    def fit(self,weights=None,y=None,start=None):
        C,S=self.stats(weights,y) if (weights is not None or y is not None) else (self.C,self.S)
        t=np.zeros(self.p) if start is None else np.array(start).copy()
        for it in range(100):
            g,H=self.derivatives(t,C,S)
            if abs(g).max()<1e-7:break
            step=solve(H,g,assume_a='pos');old=self.objective(t,C,S);alpha=1.
            # Avoid floating objective loss near optimum, accept a tiny Newton decrement.
            if g@step<1e-13:
                t-=step;break
            while self.objective(t-alpha*step,C,S)>old-1e-4*alpha*(g@step):
                alpha*=.5
                if alpha<1e-10:raise RuntimeError('line search stalled')
            t-=alpha*step
        t[:self.m]-=t[:self.m].mean()
        g,H=self.derivatives(t,C,S)
        if abs(g).max()>3e-6:raise RuntimeError(f'unconverged gradient {abs(g).max()}')
        return Fit(t,H,float(self.objective(t,C,S)),float(abs(g).max()),it+1)
    def influence(self,fit,i,j,operation='delete'):
        c=np.zeros(self.p);c[i]=1;c[j]=-1
        v=solve(fit.hessian,c,assume_a='pos')
        xv=(self.X@v)[self.group]
        prob=expit(self.X@fit.theta)[self.group]
        if operation=='delete':return (prob-self.y)*xv
        if operation=='flip':return (1-2*self.y)*xv
        raise ValueError(operation)
    def components(self,deleted=()):
        w=np.ones(self.n);w[np.asarray(deleted,dtype=int)]=0
        C,_=self.stats(w); mask=C>0
        aa=self.edges[mask,0].astype(int);bb=self.edges[mask,1].astype(int)
        A=csr_matrix((np.ones(2*len(aa)),(np.r_[aa,bb],np.r_[bb,aa])),shape=(self.m,self.m))
        return int(connected_components(A,directed=False,return_labels=False))
    def refit(self,fit,selected,operation='delete'):
        selected=np.asarray(selected,dtype=int)
        if operation=='delete':
            w=np.ones(self.n);w[selected]=0
            return self.fit(weights=w,start=fit.theta)
        yy=self.y.copy();yy[selected]=1-yy[selected]
        return self.fit(y=yy,start=fit.theta)

def ranking(t):return np.argsort(-np.asarray(t),kind='stable')

def metrics(base,t):
    m=len(base); order=ranking(base);r0=np.empty(m,int);r0[order]=np.arange(m)
    r=np.empty(m,int);r[ranking(t)]=np.arange(m)
    inversions=np.sum(np.triu((base[:,None]-base[None,:])*(t[:,None]-t[None,:])<0,1))
    return dict(top1_changed=int(r[order[0]]!=0),kendall_distance=float(inversions/(m*(m-1)/2)),max_rank_move=int(abs(r-r0).max()))
