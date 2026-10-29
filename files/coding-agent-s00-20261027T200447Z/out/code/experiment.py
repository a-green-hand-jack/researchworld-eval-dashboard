"""CPU-only, deterministic synthetic cover-time experiment; no network access."""
import argparse
import csv
import ctypes
import json
import platform
import subprocess
import time
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
SEED = 20261027
SIZES = [6, 8, 10, 12, 16, 20, 24, 30]
TRAIN_SIZES = [6, 10, 16, 24]
FAMILIES = ['path', 'cycle', 'star', 'complete', 'ladder', 'tree', 'ER', 'lollipop', 'barbell']

def generate_graphs():
    rng = np.random.default_rng(SEED)
    for n in SIZES:
        for family in FAMILIES:
            for rep in range(5 if family in ['tree', 'ER'] else 1):
                gs = int(rng.integers(1, 2**31-1))
                if family == 'path': g = nx.path_graph(n)
                elif family == 'cycle': g = nx.cycle_graph(n)
                elif family == 'star': g = nx.star_graph(n-1)
                elif family == 'complete': g = nx.complete_graph(n)
                elif family == 'ladder': g = nx.ladder_graph(n//2)
                elif family == 'tree': g = nx.random_labeled_tree(n, seed=gs)
                elif family == 'ER':
                    # Independent G(n,p) draws, conditioned on connectedness.
                    er_rng = np.random.default_rng(gs)
                    while True:
                        g = nx.gnp_random_graph(n, min(0.6, 3/n), seed=int(er_rng.integers(2**31-1)))
                        if nx.is_connected(g): break
                elif family == 'lollipop': g = nx.lollipop_graph(2*n//3, n-2*n//3)
                else: g = nx.barbell_graph(n//3, n-2*(n//3))
                assert len(g) == n and nx.is_connected(g)
                yield f'{family}_{n}_{rep}', family, gs, g

def model():
    return make_pipeline(StandardScaler(), Ridge(alpha=1.0))

def features(rows):
    return np.log([[r['n'], 2*r['m']/r['n'], r['max_degree'], r['diameter']] for r in rows])

def exact_mean(family, n):
    L = n-1
    H = sum(1/k for k in range(1, n))
    if family == 'path': return L*(7*L-1)/6
    if family == 'cycle': return n*(n-1)/2
    if family == 'complete': return L*H
    if family == 'star': return ((2*L*H-1) + L*2*L*(H-1/L))/n
    return None

def metrics(y, p, rng, B=2000):
    ape = np.abs(p/y-1)*100
    ix = rng.integers(0, len(y), size=(B, len(y)))
    return {'mape': float(ape.mean()), 'median_ape': float(np.median(ape)),
            'p90_ape': float(np.quantile(ape, .9)),
            'bias_pct': float(np.mean(p/y-1)*100),
            'mape_graph_bootstrap_95': np.quantile(ape[ix].mean(axis=1), [.025,.975]).tolist()}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--walks', type=int, default=8192)
    parser.add_argument('--reuse', action='store_true', help='reuse saved Monte Carlo draws')
    args = parser.parse_args()
    if args.walks < 2:
        parser.error('--walks must be at least 2')
    t0 = time.perf_counter()
    out = ROOT/'results'
    out.mkdir(exist_ok=True)
    subprocess.run(['gcc','-O3','-std=c99','-shared','-fPIC',str(ROOT/'simulator.c'),'-o',str(ROOT/'simulator.so')],check=True)
    lib = ctypes.CDLL(str(ROOT/'simulator.so'))
    lib.simulate.argtypes = [ctypes.c_int, np.ctypeslib.ndpointer(np.int32, flags='C_CONTIGUOUS'),
        np.ctypeslib.ndpointer(np.int32, flags='C_CONTIGUOUS'), ctypes.c_int, ctypes.c_uint64,
        np.ctypeslib.ndpointer(np.uint64, flags='C_CONTIGUOUS')]
    lib.simulate.restype = None
    cache = np.load(out/'walks.npz') if args.reuse else None
    previous = json.loads((out/'summary.json').read_text()) if args.reuse else None
    rows, manifest, draws, validation = [], [], {}, []
    for idx, (gid, family, gs, g) in enumerate(generate_graphs()):
        n = len(g)
        adj = [sorted(g[v]) for v in range(n)]
        offsets = np.array([0]+list(np.cumsum([len(a) for a in adj])), dtype=np.int32)
        neighbors = np.array([v for a in adj for v in a],dtype=np.int32)
        walk_seed = SEED + 1000003*(idx+1)
        samples = cache[gid].copy() if cache is not None else np.zeros(args.walks,dtype=np.uint64)
        assert len(samples) == args.walks
        if cache is None: lib.simulate(n,offsets,neighbors,args.walks,walk_seed,samples)
        draws[gid] = samples
        mean, se = float(samples.mean()), float(samples.std(ddof=1)/np.sqrt(len(samples)))
        row = {'id':gid,'family':family,'n':n,'m':g.number_of_edges(),
               'max_degree':max(dict(g.degree()).values()),'diameter':nx.diameter(g),
               'train':n in TRAIN_SIZES,'mean':mean,'se':se,'ci_low':mean-1.96*se,'ci_high':mean+1.96*se}
        rows.append(row)
        manifest.append({'id':gid,'graph_seed':gs,'walk_seed':walk_seed,'edges':sorted([sorted(e) for e in g.edges()])})
        exact = exact_mean(family,n)
        if exact is not None:
            validation.append({'id':gid,'exact':exact,'estimate':mean,'se':se,'z':(mean-exact)/se})
        assert samples.min() >= n-1
    if cache is None: np.savez_compressed(out/'walks.npz',**draws)
    (out/'graphs.json').write_text(json.dumps(manifest,indent=2))
    graph_simulation_seconds = time.perf_counter()-t0
    X = features(rows)
    y = np.array([r['mean'] for r in rows])
    se = np.array([r['se'] for r in rows])
    tr = np.array([r['train'] for r in rows])
    te = ~tr
    family = np.array([r['family'] for r in rows])
    base = np.array([r['n']*np.log(r['n']) for r in rows])
    upper = np.array([2*r['m']*(r['n']-1) for r in rows])
    fit = model().fit(X[tr],np.log(y[tr]))
    pred = np.exp(fit.predict(X))
    scale = np.exp(np.mean(np.log(y[tr]/base[tr])))
    lofo = np.empty_like(y)
    lofo_base = np.empty_like(y)
    for f in FAMILIES:
        test = family == f
        m = model().fit(X[~test],np.log(y[~test]))
        lofo[test] = np.exp(m.predict(X[test]))
        lofo_base[test] = base[test]*np.exp(np.mean(np.log(y[~test]/base[~test])))
    rng = np.random.default_rng(SEED+999)
    results = {'seed':SEED,'walks_per_graph':args.walks,'graphs':len(rows),
               'train_graphs':int(tr.sum()),'test_graphs':int(te.sum()),
               'sizes':SIZES,'train_sizes':TRAIN_SIZES,'features':['log n','log mean degree','log max degree','log diameter'],
               'ridge_alpha':1.0, 'scale_nlogn':float(scale),
               'size_holdout':{k:metrics(y[te],v[te],rng) for k,v in [('upper',upper),('nlogn',scale*base),('ridge',pred)]},
               'family_holdout':{k:metrics(y,v,rng) for k,v in [('nlogn',lofo_base),('ridge',lofo)]},
               'by_family':{},'validation':validation,
               'mc_relative_halfwidth_pct':{'median':float(np.median(1.96*se/y)*100),'max':float(np.max(1.96*se/y)*100)}}
    # Conditional MC uncertainty, including noisy training means and refitting.
    mc_metrics = []
    for b in range(500):
        yb = np.maximum(rng.normal(y,se),1e-8)
        mb = model().fit(X[tr],np.log(yb[tr]))
        pb = np.exp(mb.predict(X[te]))
        mc_metrics.append(np.mean(np.abs(pb/yb[te]-1))*100)
    results['size_holdout']['ridge']['mape_mc_95'] = np.quantile(mc_metrics,[.025,.975]).tolist()
    coef = fit.named_steps['ridge'].coef_/fit.named_steps['standardscaler'].scale_
    intercept = fit.named_steps['ridge'].intercept_-np.dot(coef,fit.named_steps['standardscaler'].mean_)
    results['fitted_log_formula'] = {'intercept':float(intercept),'coefficients':coef.tolist()}
    for f in FAMILIES:
        mask = family == f
        results['by_family'][f] = {'size':metrics(y[mask&te],pred[mask&te],rng),
                                   'lofo':metrics(y[mask],lofo[mask],rng)}
    for i,r in enumerate(rows):
        r.update(upper=int(upper[i]),nlogn=float(scale*base[i]),ridge=float(pred[i]),lofo=float(lofo[i]))
    with (out/'graph_results.csv').open('w') as handle:
        writer = csv.DictWriter(handle,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    results['runtime_seconds'] = time.perf_counter()-t0
    results['runtime_mode'] = 'reuse_saved_walks' if args.reuse else 'fresh_simulation'
    results['graph_simulation_seconds'] = (previous.get('graph_simulation_seconds') if args.reuse else graph_simulation_seconds)
    results['environment'] = {'python':platform.python_version(),'numpy':np.__version__,'networkx':nx.__version__}
    (out/'summary.json').write_text(json.dumps(results,indent=2))
    # Plot all held-out predictions; MC intervals are usually smaller than markers.
    plt.rcParams.update({'font.size':8,'pdf.fonttype':42})
    fig,axes = plt.subplots(1,2,figsize=(6.5,2.45))
    colors = plt.get_cmap('tab10')
    for j,f in enumerate(FAMILIES):
        mask = (family==f)&te
        axes[0].errorbar(y[mask],pred[mask],xerr=1.96*se[mask],fmt='o',ms=3,color=colors(0),alpha=.8,lw=.6)
    lim = [min(y[te].min(),pred[te].min())*.8,max(y[te].max(),pred[te].max())*1.3]
    axes[0].plot(lim,lim,'k--',lw=.8)
    axes[0].set(xscale='log',yscale='log',xlim=lim,ylim=lim,xlabel='Monte Carlo mean (steps)',ylabel='Predicted mean (steps)',title='Held-out sizes')
    xx = np.arange(len(FAMILIES))
    axes[1].bar(xx-.18,[results['by_family'][f]['size']['mape'] for f in FAMILIES],.36,label='Held-out sizes')
    axes[1].bar(xx+.18,[results['by_family'][f]['lofo']['mape'] for f in FAMILIES],.36,label='Held-out family')
    axes[1].set(xticks=xx,xticklabels=FAMILIES,ylabel='Mean absolute percentage error (%)',title='Errors depend on graph family')
    axes[1].tick_params(axis='x',rotation=55)
    axes[1].legend(fontsize=6)
    fig.tight_layout(pad=.7)
    fig.savefig(out/'prediction.pdf',bbox_inches='tight')
    fig.savefig(out/'prediction.png',dpi=180,bbox_inches='tight')
    print(json.dumps({k:v for k,v in results.items() if k not in ['validation','by_family']},indent=2))
    print('Family MAPE (size, family holdout):')
    for f in FAMILIES: print(f,results['by_family'][f]['size']['mape'],results['by_family'][f]['lofo']['mape'])
    print('Maximum exact-reference |z|:',max(abs(v['z']) for v in validation))

if __name__ == '__main__': main()
