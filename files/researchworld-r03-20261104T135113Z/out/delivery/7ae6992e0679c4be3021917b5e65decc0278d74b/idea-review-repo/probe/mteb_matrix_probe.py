import json,os,glob,collections,sys
import numpy as np
root=glob.glob('/hutian/probe/mteb/x/results-*/results')[0]
rows={}; tasks=collections.Counter(); nofile=0; bad=0
for m in sorted(os.listdir(root)):
    p=os.path.join(root,m)
    if not os.path.isdir(p): continue
    revs=sorted(os.listdir(p))
    best={}
    for r in revs:
        for f in glob.glob(os.path.join(p,r,'*.json')):
            t=os.path.basename(f)[:-5]
            if t=='model_meta': continue
            try: d=json.load(open(f))
            except Exception: bad+=1; continue
            sc=d.get('scores',{})
            # first split with a main_score, prefer test
            val=None
            for sp in ['test','validation','dev']+list(sc):
                if sp in sc and sc[sp] and isinstance(sc[sp],list) and 'main_score' in sc[sp][0]:
                    val=float(np.mean([e['main_score'] for e in sc[sp]])); break
            if val is not None: best.setdefault(t,[]).append(val)
    rows[m]={t:float(np.mean(v)) for t,v in best.items()}
    for t in rows[m]: tasks[t]+=1
print('models',len(rows),'tasks',len(tasks),'bad',bad)
cnt=np.array([len(v) for v in rows.values()])
print('tasks per model quantiles',np.percentile(cnt,[0,10,25,50,75,90,100]))
for th in [20,50,100,150]:
    ms=[m for m,v in rows.items() if len(v)>=th]; print('models with>=',th,len(ms))
tc=np.array(sorted(tasks.values(),reverse=True)); print('task coverage (n models) top',tc[:5],'median',np.median(tc))
# dense submatrix: greedy
T=sorted(tasks); M=sorted(rows)
X=np.full((len(M),len(T)),np.nan)
for i,m in enumerate(M):
    for t,v in rows[m].items(): X[i,T.index(t)]=v
print('overall fill',np.isfinite(X).mean())
for tmin in [100,200,300,400]:
    tt=np.where(np.isfinite(X).sum(0)>=tmin)[0]
    sub=X[:,tt]; mm=np.where(np.isfinite(sub).sum(1)>=0.8*len(tt))[0]
    print('tasks with>=%d models: %d; models covering>=80%% of them: %d; fill %.3f'%(tmin,len(tt),len(mm),np.isfinite(sub[mm]).mean() if len(mm) else 0))
np.save('/hutian/probe/X.npy',X); json.dump({'M':M,'T':T},open('/hutian/probe/axes.json','w'))
