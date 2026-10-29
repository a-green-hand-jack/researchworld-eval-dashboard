"""CPU-only fixed-design cover-time experiment. No external data or model tuning."""
from pathlib import Path
import csv,json,subprocess,time,platform
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'; OUT.mkdir(exist_ok=True)
SEED=20261027; TRIALS=4000
rng=np.random.default_rng(SEED)
records=[]; graphs=[]
def add(g,family,n,rep=0):
 g=nx.convert_node_labels_to_integers(g)
 assert len(g)==n and nx.is_connected(g)
 idx=len(graphs); graphs.append(g)
 split='ood' if family in ['barbell','lollipop'] else ('test' if n in [16,28] else 'train')
 records.append(dict(id=idx,family=family,n=n,rep=rep,split=split,m=g.number_of_edges(),
  diameter=nx.diameter(g),max_degree=max(dict(g.degree()).values()),
  mean_degree=2*g.number_of_edges()/n,seed=SEED+100003*(idx+1)))
for n in [8,12,16,20,24,28]:
 for f,gen in [('path',nx.path_graph),('cycle',nx.cycle_graph),('star',lambda n:nx.star_graph(n-1)),('clique',nx.complete_graph),('grid',lambda n:nx.grid_2d_graph(4,n//4))]:add(gen(n),f,n)
 for rep in range(3):
  # Connected G(n,p), rejection sampling; p fixed by n.
  while True:
   g=nx.gnp_random_graph(n, min(0.8,3/(n-1)),seed=int(rng.integers(2**31)))
   if nx.is_connected(g):break
  add(g,'er',n,rep)
  add(nx.from_prufer_sequence(rng.integers(n,size=n-2).tolist()),'tree',n,rep)
 add(nx.barbell_graph(max(3,n//4),n-2*max(3,n//4)),'barbell',n)
 add(nx.lollipop_graph(n//2,n-n//2),'lollipop',n)
# Guard against accidental structural duplicates across the fixed split.
training_graphs=[g for r,g in zip(records,graphs) if r['split']=='train']
assert all(not any(nx.is_isomorphic(g,t) for t in training_graphs)
           for r,g in zip(records,graphs) if r['split']!='train')
(OUT/'graphs.json').write_text(json.dumps([dict(**r,edges=list(g.edges())) for r,g in zip(records,graphs)],indent=2))
with open(OUT/'graphs.txt','w') as f:
 f.write(str(len(graphs))+'\n')
 for r,g in zip(records,graphs):
  f.write(f"{r['n']} {r['m']} {r['seed']}\n")
  for a,b in g.edges():f.write(f'{a} {b}\n')
t0=time.perf_counter()
subprocess.run(['g++','-O3','-std=c++17',str(ROOT/'simulate.cpp'),'-o',str(OUT/'simulate')],check=True)
subprocess.run([str(OUT/'simulate'),str(OUT/'graphs.txt'),str(OUT/'walks.csv'),str(TRIALS)],check=True)
sim_seconds=time.perf_counter()-t0
raw=np.loadtxt(OUT/'walks.csv',delimiter=',')
y=raw.mean(axis=1); se=raw.std(axis=1,ddof=1)/np.sqrt(TRIALS)
for i,r in enumerate(records):
 r.update(cover_mean=y[i],mc_se=se[i],mc_ci_low=y[i]-1.96*se[i],mc_ci_high=y[i]+1.96*se[i])
X=np.log(np.array([[r[k] for k in ['n','mean_degree','diameter','max_degree']] for r in records]))
train=np.array([r['split']=='train' for r in records]); mu=X[train].mean(0); sd=X[train].std(0)
Z=np.column_stack([np.ones(len(X)),(X-mu)/sd])
penalty=np.diag([0,1,1,1,1])
A=np.linalg.solve(Z[train].T@Z[train]+penalty,Z[train].T)
beta=A@np.log(y[train]); pred=np.exp(Z@beta)
base=np.array([r['n']*np.log(r['n']) for r in records]); a=np.exp(np.mean(np.log(y[train]/base[train])))
models={'statistics':pred,'size_only':a*base,'bound':np.array([2*r['m']*(r['n']-1) for r in records])}
for i,r in enumerate(records):
 for model,p in models.items():r[model]=p[i]
# Graph-resampling intervals: conditional on the fitted model and this design.
bootstrap=np.random.default_rng(SEED+1); metrics={}
for split in ['test','ood']:
 ix=np.flatnonzero([r['split']==split for r in records]); metrics[split]={}
 for name,p in models.items():
  err=100*np.abs(p[ix]/y[ix]-1)
  boot=err[bootstrap.integers(len(ix),size=(4000,len(ix)))].mean(1)
  metrics[split][name]={'mape':err.mean(),'graph_boot_ci':np.quantile(boot,[.025,.975]).tolist(),
   'median_ape':np.median(err),'max_ape':max(err),'bias_pct':100*np.mean(p[ix]/y[ix]-1)}
# Propagate MC label uncertainty, refitting coefficients each time; no graph resampling.
perturbed=np.maximum(1,y[:,None]+se[:,None]*bootstrap.normal(size=(len(y),2000)))
ppert=np.exp(Z@(A@np.log(perturbed[train])))
for split in ['test','ood']:
 ix=np.flatnonzero([r['split']==split for r in records])
 mc=100*np.abs(ppert[ix]/perturbed[ix]-1).mean(0)
 metrics[split]['statistics']['mc_only_ci']=np.quantile(mc,[.025,.975]).tolist()
family=[]
for f in dict.fromkeys(r['family'] for r in records):
 ix=np.array([i for i,r in enumerate(records) if r['family']==f and r['split']!='train'])
 family.append(dict(family=f,count=len(ix),mape=100*np.mean(abs(pred[ix]/y[ix]-1)),
  bias_pct=100*np.mean(pred[ix]/y[ix]-1),mean_ratio=np.mean(pred[ix]/y[ix])))
validation=[]
for i,r in enumerate(records):
 n=r['n']; exact=None
 if r['family']=='path':exact=(n-1)*(7*(n-1)-1)/6
 if r['family']=='clique':exact=(n-1)*sum(1/k for k in range(1,n))
 if r['family']=='cycle':exact=n*(n-1)/2
 if exact is not None:validation.append(dict(id=i,family=r['family'],n=n,exact=exact,estimate=y[i],z=(y[i]-exact)/se[i]))
raw_beta=beta[1:]/sd; raw_intercept=beta[0]-mu@raw_beta
summary=dict(seed=SEED,trials=TRIALS,graphs=len(graphs),train_count=int(train.sum()),
 sim_seconds=sim_seconds,python=platform.python_version(),metrics=metrics,family=family,
 model=dict(intercept=raw_intercept,coefficients=dict(zip(['log_n','log_mean_degree','log_diameter','log_max_degree'],raw_beta)),ridge=1,size_scale=a),
 mc_relative_halfwidth_pct=dict(median=float(np.median(196*se/y)),maximum=float(np.max(196*se/y))),
 validation=validation,validation_max_abs_z=max(abs(r['z']) for r in validation))
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
with open(OUT/'estimates.csv','w') as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
fig,axes=plt.subplots(1,2,figsize=(7.0,2.55),layout='constrained')
colors=plt.get_cmap('tab10')
for j,row in enumerate(family):
 f=row['family'];ix=np.array([i for i,r in enumerate(records) if r['family']==f and r['split']!='train'])
 axes[0].errorbar(y[ix],pred[ix],xerr=1.96*se[ix],fmt='s' if f in ['barbell','lollipop'] else 'o',ms=3,color=colors(j),label=f,capsize=1,lw=.5)
 axes[1].bar(j,row['mean_ratio'],color=colors(j))
lims=[15,6000];axes[0].plot(lims,lims,'k--',lw=.7);axes[0].set(xscale='log',yscale='log',xlabel='Simulated cover time',ylabel='Predicted cover time',xlim=lims,ylim=lims)
axes[0].legend(fontsize=5,ncol=2,loc='upper left',frameon=False)
axes[1].axhline(1,color='black',ls='--',lw=.7);axes[1].set_xticks(range(len(family)),[r['family'] for r in family],rotation=45,ha='right',fontsize=7);axes[1].set_ylabel('Mean prediction / simulation')
for ax in axes:ax.tick_params(labelsize=7)
fig.savefig(OUT/'prediction.pdf');fig.savefig(OUT/'prediction.png',dpi=160)
print(json.dumps(summary,indent=2))
