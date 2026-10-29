"""Convex Bradley--Terry fit and fixed-schedule outcome-reversal audits."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.linalg import solve

@dataclass
class Data:
    name:str
    frame:pd.DataFrame
    def __post_init__(self):
        d=self.frame.reset_index(drop=True);self.frame=d
        self.names=np.array(sorted(set(d.a)|set(d.b)));self.m=len(self.names);self.n=len(d)
        idx={s:i for i,s in enumerate(self.names)}
        self.a=d.a.map(idx).to_numpy();self.b=d.b.map(idx).to_numpy();self.y=d.y.to_numpy(float)
        assert np.all(self.a<self.b)
        pairs=np.unique(np.c_[self.a,self.b],axis=0);self.ea=pairs[:,0];self.eb=pairs[:,1];self.e=len(pairs)
        lookup={tuple(v):i for i,v in enumerate(pairs)};self.edge=np.array([lookup[(a,b)] for a,b in zip(self.a,self.b)])
        self.count=np.bincount(self.edge,minlength=self.e).astype(float)
        self.wins=np.bincount(self.edge,weights=self.y,minlength=self.e)
        self.X=np.zeros((self.e,self.m));self.X[np.arange(self.e),self.ea]=1;self.X[np.arange(self.e),self.eb]=-1
        self.dec=np.flatnonzero(self.y!=.5)
        self.cluster=pd.factorize(d.cluster)[0];self.clusters=int(self.cluster.max()+1)
    def aggregate(self,weights):
        return np.bincount(self.edge,weights=weights,minlength=self.e),np.bincount(self.edge,weights=weights*self.y,minlength=self.e)
    def fit(self,wins=None,count=None,lam=.001,start=None):
        w=self.wins if wins is None else wins;n=self.count if count is None else count
        t=np.zeros(self.m) if start is None else np.array(start).copy();t-=t.mean()
        def obj(v):
            z=v[self.ea]-v[self.eb]
            return np.sum(n*np.logaddexp(0,z)-w*z)+lam*np.dot(v,v)/2
        val=obj(t)
        for it in range(100):
            p=expit(t[self.ea]-t[self.eb]);r=n*p-w
            grad=self.X.T@r+lam*t
            if np.max(np.abs(grad))<1e-8:break
            H=(self.X.T*(n*p*(1-p)))@self.X+lam*np.eye(self.m)
            # Stabilize the irrelevant constant direction without changing the centered solution.
            H+=np.ones((self.m,self.m))/self.m
            step=solve(H,grad,assume_a='pos');step-=step.mean()
            scale=1.
            while scale>2**-25:
                v=t-scale*step;new=obj(v)
                if new<=val-1e-4*scale*np.dot(grad,step)+1e-10:break
                scale*=.5
            t=v;val=new
        else:raise RuntimeError(f'Newton failed {self.name}: {np.max(np.abs(grad))}')
        if not np.isfinite(t).all():raise RuntimeError('nonfinite')
        return t
    def hessian(self,t,lam=.001):
        p=expit(t[self.ea]-t[self.eb]);return (self.X.T*(self.count*p*(1-p)))@self.X+lam*np.eye(self.m)+np.ones((self.m,self.m))/self.m
    def influence(self,t,i,j,lam=.001):
        c=np.zeros(self.m);c[i]=1;c[j]=-1
        v=solve(self.hessian(t,lam),c,assume_a='pos')
        # Positive gain means a reduction of theta_i - theta_j.
        return -(1-2*self.y)*(v[self.a]-v[self.b])
    def edited_wins(self,ids):
        ids=np.asarray(ids,dtype=int)
        return self.wins+np.bincount(self.edge[ids],weights=1-2*self.y[ids],minlength=self.e)
    def win_totals(self):
        return np.bincount(self.a,weights=self.y,minlength=self.m)+np.bincount(self.b,weights=1-self.y,minlength=self.m)
    def order(self,t,i,j,mode='influence',lam=.001):
        gain=self.influence(t,i,j,lam);ids=self.dec
        if mode=='endpoint':ids=ids[np.isin(self.a[ids],[i,j])|np.isin(self.b[ids],[i,j])]
        if mode=='direct':ids=ids[(self.a[ids]==min(i,j))&(self.b[ids]==max(i,j))]
        if mode=='wins':
            gain=(2*self.y-1)*((self.a==i).astype(int)-(self.a==j).astype(int)-(self.b==i).astype(int)+(self.b==j).astype(int))
        ids=ids[gain[ids]>1e-12]
        return ids[np.argsort(-gain[ids],kind='stable')],gain
    def audit(self,t,i,j,mode='influence',lam=.001,max_fraction=.2):
        ids,gain=self.order(t,i,j,mode,lam);limit=min(len(ids),int(np.ceil(max_fraction*self.n)))
        gap=t[i]-t[j];s=np.cumsum(gain[ids]);ix=np.flatnonzero(s>gap)
        pred=int(ix[0]+1) if len(ix) and mode!='wins' else None
        w=self.wins.copy();cur=t.copy();first=None;before=gap
        for k,r in enumerate(ids[:limit],1):
            w[self.edge[r]]+=1-2*self.y[r];cur=self.fit(wins=w,lam=lam,start=cur)
            after=float(cur[i]-cur[j])
            if after < -1e-9:first=k;break
            before=after
        exposure=int(np.count_nonzero(np.isin(self.a,[i,j])|np.isin(self.b,[i,j])))
        return {'mode':mode,'k':first,'limit':limit,'predicted_k':pred,'gap':float(gap),'before_gap':float(before),'after_gap':float(cur[i]-cur[j]),'exposure':exposure,'edited_ids':ids[:first].tolist() if first else [],'indirect':int(np.sum(~(np.isin(self.a[ids[:first]],[i,j])|np.isin(self.b[ids[:first]],[i,j])))) if first else None}
    def balanced_radius(self,i,j):
        mat=np.zeros((self.m,self.m));mat[self.ea,self.eb]=self.count;mat+=mat.T
        other=[k for k in range(self.m) if k not in [i,j]]
        if not np.all(mat[i,other]==mat[j,other]):raise ValueError('not pair-balanced')
        margin=self.win_totals()[i]-self.win_totals()[j]
        gain=(2*self.y-1)*((self.a==i).astype(int)-(self.a==j).astype(int)-(self.b==i).astype(int)+(self.b==j).astype(int))
        vals=np.sort(gain[gain>0])[::-1];cross=np.flatnonzero(np.cumsum(vals)>margin+1e-9)
        return int(cross[0]+1) if len(cross) else None
