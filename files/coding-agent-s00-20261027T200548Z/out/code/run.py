"""Small CPU experiment. No external data or research-page access."""
import argparse
import csv
import json
import math
import platform
import subprocess
import time
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parent
FAMILIES = ['path','cycle','star','clique','grid','ER_sparse','ER_dense',
            'random_tree','lollipop','barbell']
SIZES = [8,12,16,20,24,28,30]
TRAIN_SIZES = [8,12,20,28]
SEED = 20261027
TRIALS = 4000
BLOCKS = 40

def graphs():
    rng = np.random.default_rng(SEED)
    records = []
    for f in FAMILIES:
        for n in SIZES:
            for rep in range(4 if f.startswith('ER') or f=='random_tree' else 1):
                seed = int(rng.integers(1,2**31-1))
                rejected = 0
                if f=='path': g=nx.path_graph(n)
                elif f=='cycle': g=nx.cycle_graph(n)
                elif f=='star': g=nx.star_graph(n-1)
                elif f=='clique': g=nx.complete_graph(n)
                elif f=='grid':
                    width=math.isqrt(n)
                    g=nx.Graph();g.add_nodes_from(range(n))
                    g.add_edges_from((v,v+1) for v in range(n-1) if (v+1)%width)
                    g.add_edges_from((v,v+width) for v in range(n-width))
                elif f.startswith('ER'):
                    local=np.random.default_rng(seed)
                    p=3/(n-1) if f=='ER_sparse' else .35
                    while True:
                        g=nx.gnp_random_graph(n,p,seed=int(local.integers(2**31-1)))
                        if nx.is_connected(g): break
                        rejected+=1
                elif f=='random_tree': g=nx.random_labeled_tree(n,seed=seed)
                elif f=='lollipop': g=nx.lollipop_graph((n+1)//2,n//2)
                elif f=='barbell': g=nx.barbell_graph(n//3,n-2*(n//3))
                g=nx.convert_node_labels_to_integers(g,ordering='sorted')
                assert len(g)==n and nx.is_connected(g) and not nx.is_directed(g)
                records.append(dict(id=len(records),family=f,n=n,m=g.number_of_edges(),
                    dmax=max(dict(g.degree()).values()),diameter=nx.diameter(g),
                    graph_seed=seed,walk_seed=SEED+100000+len(records),rep=rep,
                    rejected=rejected,edges=sorted([sorted(e) for e in g.edges()]),
                    split='train' if n in TRAIN_SIZES else 'test'))
    return records

def design(records, features):
    return np.log(np.array([[r[k] for k in features] for r in records],float))

def weights(records, mask):
    counts={f:sum(mask[i] and r['family']==f for i,r in enumerate(records))
            for f in FAMILIES}
    return np.array([1/counts[r['family']] if mask[i] else 0.
                     for i,r in enumerate(records)])

def fit_predict(x,y,train,records):
    # Weighted log-space ridge; scale using training graphs only.
    w=weights(records,train);w=w/w.sum()
    center=w@x;scale=np.sqrt(w@((x-center)**2));scale[scale<1e-12]=1
    z=np.column_stack([np.ones(len(x)),(x-center)/scale])
    # Equal total family weight and lambda=.01 in weighted mean loss.
    penalty=np.diag([0]+[.01]*x.shape[1])
    beta=np.linalg.solve(z.T@(w[:,None]*z)+penalty,z.T@(w*np.log(y)))
    return np.exp(z@beta),dict(center=center.tolist(),scale=scale.tolist(),
                               coefficients=beta.tolist(),lambda_value=.01)

def metric(pred,y,records,mask):
    w=weights(records,mask);w=w/w.sum()
    return dict(mape=100*float(w@np.abs(pred/y-1)),
                factor=float(np.exp(w@np.abs(np.log(pred/y)))))

def evaluate(records,y):
    train=np.array([r['split']=='train' for r in records]);test=~train
    xs={'size':design(records,['n']),
        'four':design(records,['n','m','dmax','diameter'])}
    preds={};fits={}
    for name,x in xs.items():preds[name],fits[name]=fit_predict(x,y,train,records)
    preds['bound']=np.array([2*r['m']*(r['n']-1) for r in records],float)
    lofo={name:np.zeros(len(records)) for name in xs}
    for family in FAMILIES:
        held=np.array([r['family']==family for r in records])
        for name,x in xs.items():
            p,_=fit_predict(x,y,~held,records);lofo[name][held]=p[held]
    scores={name:metric(p,y,records,test) for name,p in preds.items()}
    for name,p in lofo.items():scores['lofo_'+name]=metric(p,y,records,np.ones(len(y),bool))
    return scores,preds,lofo,fits

def exact_value(r):
    n=r['n'];h=sum(1/k for k in range(1,n))
    if r['family']=='clique':return (n-1)*h
    if r['family']=='path':return (n-1)**2+(n-1)*(n-2)/6
    if r['family']=='star':return 2*(n-1)*h-(2*n-1)/n
    return None

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reuse',action='store_true')
    parser.add_argument('--bootstrap',type=int,default=500);args=parser.parse_args()
    begin=time.perf_counter();out=ROOT/'results';out.mkdir(exist_ok=True)
    (ROOT/'figures').mkdir(exist_ok=True)
    records=graphs();(out/'graphs.json').write_text(json.dumps(records,indent=2)+'\n')
    if not args.reuse:
        lines=[str(len(records))]
        for r in records:
            lines.append(f"{r['n']} {r['m']} {TRIALS} {r['walk_seed']}")
            lines.extend(f'{u} {v}' for u,v in r['edges'])
        (out/'simulation_input.txt').write_text('\n'.join(lines)+'\n')
        subprocess.run(['g++','-O3','-std=c++17',str(ROOT/'simulate.cpp'),'-o',str(ROOT/'simulate')],check=True)
        start=time.perf_counter()
        subprocess.run([str(ROOT/'simulate'),str(out/'simulation_input.txt'),str(out/'cover_times.txt')],check=True)
        simulation_seconds=time.perf_counter()-start
    else:
        old=json.loads((out/'summary.json').read_text()) if (out/'summary.json').exists() else {}
        simulation_seconds=old.get('simulation_seconds')
    raw=np.loadtxt(out/'cover_times.txt',dtype=np.int64)
    assert raw.shape==(len(records),TRIALS) and np.all(raw>=np.array([r['n']-1 for r in records])[:,None])
    y=raw.mean(axis=1);se=raw.std(axis=1,ddof=1)/np.sqrt(TRIALS)
    scores,preds,lofo,fits=evaluate(records,y)
    rng=np.random.default_rng(SEED+2)
    block_means=raw.reshape(len(records),BLOCKS,-1).mean(axis=2)
    boot={name:{k:[] for k in ['mape','factor']} for name in scores}
    family_boot={f:[] for f in FAMILIES}
    for b in range(args.bootstrap):
        indices=rng.integers(0,BLOCKS,(len(records),BLOCKS))
        yy=np.take_along_axis(block_means,indices,axis=1).mean(axis=1)
        ss,pp,_,_=evaluate(records,yy)
        for name in boot:
            for k in boot[name]:boot[name][k].append(ss[name][k])
        for f in FAMILIES:
            mask=np.array([r['family']==f and r['split']=='test' for r in records])
            family_boot[f].append(metric(pp['four'],yy,records,mask)['mape'])
    for name in scores:
        scores[name]['mc95']={k:np.quantile(v,[.025,.975]).tolist() for k,v in boot[name].items()}
    family=[]
    for f in FAMILIES:
        test=np.array([r['family']==f and r['split']=='test' for r in records])
        allf=np.array([r['family']==f for r in records])
        family.append(dict(family=f,count=int(test.sum()),
            four=metric(preds['four'],y,records,test)['mape'],
            size=metric(preds['size'],y,records,test)['mape'],
            bound=metric(preds['bound'],y,records,test)['mape'],
            signed=100*float(np.mean(preds['four'][test]/y[test]-1)),
            lofo_four=metric(lofo['four'],y,records,allf)['mape'],
            mc95=np.quantile(family_boot[f],[.025,.975]).tolist()))
    validation=[]
    for i,r in enumerate(records):
        exact=exact_value(r)
        if exact is not None:
            validation.append(dict(id=i,family=r['family'],n=r['n'],exact=exact,
                                   estimate=y[i],se=se[i],z=(y[i]-exact)/se[i]))
    with (out/'estimates.csv').open('w') as fp:
        keys=['id','family','n','m','dmax','diameter','split','mean','se','ci_low','ci_high',
              'pred_four','pred_size','bound','lofo_four']
        writer=csv.DictWriter(fp,fieldnames=keys);writer.writeheader()
        critical=student_t.ppf(.975,TRIALS-1)
        for i,r in enumerate(records):
            row={k:r[k] for k in keys if k in r};row.update(mean=y[i],se=se[i],
                ci_low=y[i]-critical*se[i],ci_high=y[i]+critical*se[i],
                pred_four=preds['four'][i],pred_size=preds['size'][i],
                bound=preds['bound'][i],lofo_four=lofo['four'][i]);writer.writerow(row)
    summary=dict(seed=SEED,trials=TRIALS,graphs=len(records),
        train_graphs=sum(r['split']=='train' for r in records),scores=scores,
        families=family,fit=fits,exact_checks=validation,
        relative_ci_halfwidth_percent=dict(median=float(np.median(1.96*se/y)*100),
                                           maximum=float(np.max(1.96*se/y)*100)),
        simulation_seconds=simulation_seconds,analysis_and_simulation_seconds=time.perf_counter()-begin,
        platform=platform.platform(),python=platform.python_version())
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'fitted_model.json').write_text(json.dumps(fits['four'],indent=2)+'\n')
    # Machine-generated LaTeX tables prevent transcription errors.
    rows=[]
    for name,label in [('bound','Upper bound'),('size','Size-only'),('four','Four statistics'),
                       ('lofo_size','LOFO size-only'),('lofo_four','LOFO four stats.')]:
        s=scores[name];a,b=s['mc95']['mape']
        rows.append(f"{label} & {s['mape']:.1f} [{a:.1f}, {b:.1f}] & {s['factor']:.2f}" + " " + chr(92)*2)
    (out/'overall_rows.tex').write_text('\n'.join(rows)+'\n')
    (out/'overall_table.tex').write_text(
        '\\begin{tabular}{lrr}\n\\toprule\nPredictor & MAPE (\\%) & Factor'+chr(92)*2+
        '\n\\midrule\n'+'\n'.join(rows)+'\n\\bottomrule\n\\end{tabular}\n')
    rows=[]
    for r in family:
        a,b=r['mc95'];label=r['family'].replace('_',' ')
        rows.append(f"{label} & {r['four']:.1f} [{a:.1f}, {b:.1f}] & {r['lofo_four']:.1f}" + " " + chr(92)*2)
    (out/'family_rows.tex').write_text('\n'.join(rows)+'\n')
    (out/'family_table.tex').write_text(
        '\\begin{tabular}{lrr}\n\\toprule\nFamily & Size test & LOFO'+chr(92)*2+
        '\n\\midrule\n'+'\n'.join(rows)+'\n\\bottomrule\n\\end{tabular}\n')
    plt.rcParams.update({'font.size':8,'pdf.fonttype':42})
    fig,axes=plt.subplots(1,2,figsize=(6.7,2.65),constrained_layout=True)
    colors=plt.get_cmap('tab10')
    for j,f in enumerate(FAMILIES):
        mask=np.array([r['family']==f and r['split']=='test' for r in records])
        axes[0].errorbar(y[mask],preds['four'][mask],xerr=1.96*se[mask],fmt='o',
                         ms=3,color=colors(j),alpha=.8,label=f.replace('_',' '))
    lim=[30,max(y.max(),preds['four'].max())*1.15]
    axes[0].plot(lim,lim,'k--',lw=.8);axes[0].set(xscale='log',yscale='log',
        xlabel='Simulated mean cover time',ylabel='Predicted cover time',xlim=lim,ylim=lim)
    axes[0].legend(fontsize=5.5,ncol=2,loc='upper left')
    xx=np.arange(len(family));values=[r['four'] for r in family]
    axes[1].bar(xx,values,color=[colors(j) for j in range(len(family))])
    # Bootstrap percentile intervals need not bracket a nonlinear point estimate.
    for j,r in enumerate(family):axes[1].vlines(j,*r['mc95'],color='black',linewidth=1)
    axes[1].set_xticks(xx,[r['family'].replace('_','\n') for r in family],rotation=65,ha='right',fontsize=6)
    axes[1].set(ylabel='Test MAPE (%)',ylim=(0,max(values)*1.16))
    fig.savefig(ROOT/'figures'/'results.pdf');plt.close(fig)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['exact_checks','fit']},indent=2))

if __name__=='__main__':main()
