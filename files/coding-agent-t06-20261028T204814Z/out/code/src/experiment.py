"""Main experiment; writes all numerical evidence (seed 20261028)."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1')
from pathlib import Path
import json,time,argparse
import numpy as np,pandas as pd
from scipy.stats import kendalltau
from bt import Data
R=Path(__file__).resolve().parents[1];SEED=20261028
NAMES=['arena','mt_human','mt_gpt4','nba2014','nba2015']
def dump(path,obj):path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def load(name):return Data(name,pd.read_csv(R/f'data/processed/{name}.csv',dtype={'cluster':str,'record_id':str}))
def main(reps,boot):
    start=time.time();summary=[];attacks=[];noise=[];bootstrap=[];curves=[];rankings=[];ablations=[];allpairs=[]
    for di,name in enumerate(NAMES):
        print('START',name,flush=True);d=load(name);t=d.fit();order=np.argsort(-t);i,j=order[:2]
        eig=np.linalg.eigvalsh(d.hessian(t)-np.ones((d.m,d.m))/d.m)
        summary.append({'dataset':name,'n':d.n,'m':d.m,'edges':d.e,'decisive':len(d.dec),'clusters':d.clusters,'leader':d.names[i],'runner':d.names[j],'gap':float(t[i]-t[j]),'algebraic_curvature':float(eig[1])})
        rankings.extend({'dataset':name,'model':d.names[k],'rank':r+1,'theta':float(t[k])} for r,k in enumerate(order))
        modes={}
        for mode in ['influence','endpoint','direct','wins']:
            a=d.audit(t,i,j,mode);a.update(dataset=name,leader=d.names[i],runner=d.names[j]);attacks.append(a);modes[mode]=a
            print(name,mode,a['k'],a['predicted_k'],flush=True)
        for lam in [.00001,.1,1.]:
            tt=d.fit(lam=lam);ii,jj=np.argsort(-tt)[:2];a=d.audit(tt,ii,jj,lam=lam)
            ablations.append({'dataset':name,'variant':'ridge','value':lam,'leader':d.names[ii],'runner':d.names[jj],'k':a['k'],'gap':float(tt[ii]-tt[jj])})
        # Drop ties (including inconsistent GPT outcomes), keeping the original named pair.
        dd=Data(name+'_decisive',d.frame[d.frame.y!=.5].copy());tt=dd.fit();ii=np.where(dd.names==d.names[i])[0][0];jj=np.where(dd.names==d.names[j])[0][0]
        aa=dd.audit(tt,ii,jj) if tt[ii]>tt[jj] else {'k':0}
        ablations.append({'dataset':name,'variant':'decisive_only','value':dd.n,'leader':d.names[i],'runner':d.names[j],'k':aa['k'],'gap':float(tt[ii]-tt[jj])})
        # Every adjacent pair among the original top ten; all challengers for leader.
        pairs=set(zip(order[:min(10,d.m)-1],order[1:min(10,d.m)]))|{(i,v) for v in order[1:]}
        for ii,jj in sorted(pairs):
            a=modes['influence'] if (ii,jj)==(i,j) else d.audit(t,ii,jj,max_fraction=.05)
            allpairs.append({'dataset':name,'i':d.names[ii],'j':d.names[jj],'rank_i':int(np.where(order==ii)[0][0]+1),'rank_j':int(np.where(order==jj)[0][0]+1),'k':a['k'],'predicted_k':a['predicted_k'],'gap':float(t[ii]-t[jj]),'exposure':a['exposure'],'limit':a['limit']})
        # Prefix trajectories at logarithmic scales, each point refitted.
        ids,gain=d.order(t,i,j);ks=sorted(set([0]+[max(1,int(np.ceil(d.n*f))) for f in [.0005,.001,.002,.005,.01,.02,.05]]+[modes['influence']['k'] or 0]))
        for k in ks:
            if k<=len(ids):
                tt=d.fit(wins=d.edited_wins(ids[:k]),start=t)
                curves.append({'dataset':name,'k':k,'gap_exact':float(tt[i]-tt[j]),'gap_linear':float(t[i]-t[j]-gain[ids[:k]].sum()),'tau':float(kendalltau(t,tt).statistic),'top_changed':int(np.argmax(tt)!=i)})
        # Independent uniform subsets at each budget, full BT refit.
        rng=np.random.default_rng(SEED+di*100)
        for k in ks[1:]:
            for rep in range(reps):
                sel=rng.choice(d.dec,k,replace=False);tt=d.fit(wins=d.edited_wins(sel),start=t)
                noise.append({'dataset':name,'k':k,'rep':rep,'gap':float(tt[i]-tt[j]),'pair_changed':int(tt[i]<tt[j]),'top_changed':int(np.argmax(tt)!=i),'tau':float(kendalltau(t,tt).statistic)})
        # Cluster bootstrap: fixed original pair, resample entire clusters.
        rng=np.random.default_rng(SEED+di*100+1)
        for rep in range(boot):
            mult=rng.multinomial(d.clusters,np.ones(d.clusters)/d.clusters);weights=mult[d.cluster];count,wins=d.aggregate(weights);tt=d.fit(count=count,wins=wins,start=t)
            bootstrap.append({'dataset':name,'rep':rep,'gap':float(tt[i]-tt[j]),'top_retained':int(np.argmax(tt)==i),'n':int(weights.sum())})
        for fn,values in [('summary',summary),('rankings',rankings),('noise',noise),('bootstrap',bootstrap),('curves',curves),('ablations',ablations),('allpairs',allpairs)]:pd.DataFrame(values).to_csv(R/f'results/{fn}.csv',index=False)
        dump(R/'results/attacks.json',attacks)
        print('DONE',name,'seconds',time.time()-start,flush=True)
    dump(R/'results/run_metadata.json',{'seed':SEED,'noise_repetitions':reps,'bootstrap_repetitions':boot,'seconds':time.time()-start,'numpy':np.__version__,'cpu_only':True})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--reps',type=int,default=500);p.add_argument('--boot',type=int,default=1000);a=p.parse_args();main(a.reps,a.boot)
