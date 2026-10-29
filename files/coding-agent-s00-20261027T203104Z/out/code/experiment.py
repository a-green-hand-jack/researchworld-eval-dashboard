"""CPU-only small-graph cover-time experiment; run from this directory."""
import os
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import csv, ctypes, json, math, subprocess, time
from pathlib import Path
import numpy as np
import networkx as nx
from scipy.stats import t
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results'
OUT.mkdir(exist_ok=True)
SEED, TRIALS, BOOT = 20261027, 8192, 300
SIZES = [6, 10, 14, 18, 22, 26, 30]
FAMILIES = ['path', 'cycle', 'star', 'complete', 'grid', 'ER', 'tree', 'lollipop', 'barbell']

def generate(f, n, seed):
    if f == 'path': g = nx.path_graph(n)
    elif f == 'cycle': g = nx.cycle_graph(n)
    elif f == 'star': g = nx.star_graph(n-1)
    elif f == 'complete': g = nx.complete_graph(n)
    elif f == 'grid':
        w = math.isqrt(n)
        g = nx.Graph()
        g.add_nodes_from(range(n))
        for v in range(n):
            if v % w and v-1 >= 0: g.add_edge(v, v-1)
            if v >= w: g.add_edge(v, v-w)
    elif f == 'ER':
        rng = np.random.default_rng(seed)
        while True:
            g = nx.gnp_random_graph(n, min(0.6, 2*math.log(n)/n), seed=int(rng.integers(2**32)))
            if nx.is_connected(g): break
    elif f == 'tree': g = nx.random_labeled_tree(n, seed=seed)
    elif f == 'lollipop': g = nx.lollipop_graph(2*n//3, n-2*n//3)
    elif f == 'barbell': g = nx.barbell_graph(n//3, n-2*(n//3))
    assert nx.is_connected(g) and len(g) == n <= 30
    return g

def exact_cover(g):
    """Subset-state linear equations, used only for n=6 validation."""
    n = len(g); full = (1 << n)-1
    values = np.zeros((1 << n, n))
    for mask in range(full-1, 0, -1):
        vertices = [v for v in g if mask >> v & 1]
        pos = {v: k for k, v in enumerate(vertices)}
        a = np.eye(len(vertices)); b = np.ones(len(vertices))
        for v in vertices:
            for w in g[v]:
                p = 1/g.degree[v]
                if mask >> w & 1: a[pos[v], pos[w]] -= p
                else: b[pos[v]] += p*values[mask | (1 << w), w]
        values[mask, vertices] = np.linalg.solve(a, b)
    return np.mean([values[1 << v, v] for v in g])

def features(rows):
    return np.log([[r['n'], 2*r['m']/r['n'], r['max_degree'], r['diameter']] for r in rows])

def fit_predict(x, y, train, test, cols):
    model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    model.fit(x[train][:, cols], np.log(y[train]))
    return np.exp(model.predict(x[test][:, cols])), model

def predictions(rows, y, family_train):
    x = features(rows); fam = np.array([r['family'] for r in rows])
    test = np.array([r['n'] in (14, 26) for r in rows])
    bound = np.array([2*r['m']*(r['n']-1) for r in rows], float)
    preds = {'interpolation': {'bound': bound.copy()}, 'leave_family_out': {'bound': bound.copy()}}
    for name, cols in [('n_only', [0]), ('four_stats', [0, 1, 2, 3])]:
        p = np.full(len(rows), np.nan)
        p[test], _ = fit_predict(x, y, ~test, test, cols)
        preds['interpolation'][name] = p
        p = np.empty(len(rows))
        for f in FAMILIES:
            held = fam == f
            p[held], _ = fit_predict(x, y, family_train[f], held, cols)
        preds['leave_family_out'][name] = p
    return preds, {'interpolation': test, 'leave_family_out': np.ones(len(rows), bool)}

def metrics(rows, y, preds, masks):
    fam = np.array([r['family'] for r in rows]); result = {}
    for protocol, methods in preds.items():
        result[protocol] = {}
        for method, p in methods.items():
            per = {}
            for f in FAMILIES:
                idx = masks[protocol] & (fam == f)
                per[f] = float(100*np.mean(np.abs(p[idx]/y[idx]-1)))
            result[protocol][method] = {'macro_mape': float(np.mean(list(per.values()))), 'family_mape': per}
    return result

def main():
    started = time.perf_counter()
    subprocess.run(['gcc', '-O3', '-std=c99', '-shared', '-fPIC', str(ROOT/'simulate.c'), '-o', str(ROOT/'simulate.so')], check=True)
    lib = ctypes.CDLL(str(ROOT/'simulate.so'))
    ptr = np.ctypeslib.ndpointer
    lib.simulate.argtypes = [ctypes.c_int, ptr(np.int32, flags='C_CONTIGUOUS'), ptr(np.int32, flags='C_CONTIGUOUS'), ctypes.c_int, ctypes.c_uint64, ptr(np.uint64, flags='C_CONTIGUOUS')]
    lib.simulate.restype = None
    rows, graphs, samples, validations, graph_objects = [], [], [], [], []
    streams = np.random.SeedSequence(SEED).spawn(189)
    for f in FAMILIES:
        for n in SIZES:
            for rep in range(10 if f in ('ER', 'tree') else 1):
                i = len(rows)
                graph_seed, walk_seed = map(int, streams[i].generate_state(2, dtype=np.uint64))
                g = generate(f, n, graph_seed)
                graph_objects.append(g)
                degree = np.array([g.degree[v] for v in range(n)], dtype=np.int32)
                adj = np.zeros((n, n), dtype=np.int32)
                for v in g: adj[v, :degree[v]] = sorted(g[v])
                times = np.empty(TRIALS, dtype=np.uint64)
                lib.simulate(n, degree, adj, TRIALS, walk_seed, times)
                mean = float(times.mean()); se = float(times.std(ddof=1)/math.sqrt(TRIALS))
                half = float(t.ppf(.975, TRIALS-1)*se)
                row = dict(id=i, family=f, n=n, replicate=rep, m=g.number_of_edges(), max_degree=int(max(degree)), diameter=nx.diameter(g), mean=mean, se=se, ci_low=mean-half, ci_high=mean+half, graph_seed=graph_seed, walk_seed=walk_seed)
                rows.append(row); samples.append(times)
                graphs.append({'id': i, 'edges': sorted([list(e) for e in g.edges()])})
                exact = None; kind = None
                if f == 'path': exact=(n-1)*(7*(n-1)-1)/6
                elif f == 'cycle': exact=n*(n-1)/2
                elif f == 'complete': exact=(n-1)*sum(1/k for k in range(1,n))
                elif f == 'star': exact=2*(n-1)*sum(1/k for k in range(1,n))-2+1/n
                if exact is not None: kind='formula'
                if n == 6 and rep == 0:
                    dp = exact_cover(g)
                    if exact is not None: assert abs(dp-exact) < 1e-8
                    exact, kind = dp, 'subset_DP'
                if exact is not None:
                    validations.append({'id':i, 'family':f, 'n':n, 'kind':kind, 'exact':exact, 'z':(mean-exact)/se})
    assert len(rows) == 189
    samples = np.array(samples)
    np.savez_compressed(OUT/'walk_times.npz', times=samples)
    (OUT/'graphs.json').write_text(json.dumps(graphs))
    with (OUT/'graphs.csv').open('w') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    y = np.array([r['mean'] for r in rows])
    hashes = [nx.weisfeiler_lehman_graph_hash(g) for g in graph_objects]
    family_train, excluded = {}, {}
    for f in FAMILIES:
        train = np.array([r['family'] != f for r in rows])
        held = np.where(~train)[0]
        for i in np.where(train)[0]:
            if any(hashes[i] == hashes[j] and nx.is_isomorphic(graph_objects[i],graph_objects[j]) for j in held):
                train[i] = False
        family_train[f] = train
        excluded[f] = int(sum(r['family'] != f for r in rows)-train.sum())
    preds, masks = predictions(rows, y, family_train)
    result = metrics(rows, y, preds, masks)
    sim_seconds = time.perf_counter()-started
    # Resample independent equal-sized batches to propagate MC uncertainty,
    # including training labels, without introducing graph-population claims.
    batches = samples.reshape(len(rows), 64, TRIALS//64).mean(axis=2)
    rng = np.random.default_rng(SEED+1)
    boot = {p:{m:[] for m in preds[p]} for p in preds}
    family_boot = {p:{f:[] for f in FAMILIES} for p in preds}
    for _ in range(BOOT):
        ix = rng.integers(64, size=(len(rows),64))
        ys = np.take_along_axis(batches, ix, axis=1).mean(axis=1)
        pp, mm = predictions(rows, ys, family_train); met = metrics(rows, ys, pp, mm)
        for p in preds:
            for m in preds[p]: boot[p][m].append(met[p][m]['macro_mape'])
            for f in FAMILIES: family_boot[p][f].append(met[p]['four_stats']['family_mape'][f])
    for p in preds:
        for m in preds[p]: result[p][m]['mc95'] = np.quantile(boot[p][m],[.025,.975]).tolist()
        result[p]['four_stats']['family_mc95'] = {f:np.quantile(v,[.025,.975]).tolist() for f,v in family_boot[p].items()}
    _, model = fit_predict(features(rows), y, ~masks['interpolation'], masks['interpolation'], [0,1,2,3])
    sc, reg = model.steps[0][1], model.steps[1][1]
    beta = reg.coef_/sc.scale_; intercept = reg.intercept_-np.dot(beta, sc.mean_)
    result['model'] = {'log_intercept':float(intercept), 'log_coefficients':beta.tolist(), 'feature_order':['n','mean_degree','max_degree','diameter']}
    result['design'] = {'seed':SEED, 'trials':TRIALS, 'bootstrap':BOOT, 'graphs':len(rows), 'train_graphs':int((~masks['interpolation']).sum()), 'test_graphs':int(masks['interpolation'].sum()), 'sizes':SIZES}
    rel = np.array([(r['ci_high']-r['mean'])/r['mean'] for r in rows])
    result['mc_precision'] = {'median_relative_halfwidth':float(np.median(rel)), 'max_relative_halfwidth':float(max(rel))}
    result['validation'] = {'checks':len(validations), 'max_abs_z':float(max(abs(v['z']) for v in validations)), 'within_95':int(sum(abs(v['z']) <= t.ppf(.975,TRIALS-1) for v in validations))}
    result['isomorphic_training_graphs_removed'] = excluded
    collisions = []
    for i in range(len(rows)):
        for j in range(i):
            if all(rows[i][k] == rows[j][k] for k in ('n','m','max_degree','diameter')) and not nx.is_isomorphic(graph_objects[i], graph_objects[j]):
                collisions.append({'ids':[j,i], 'ratio':float(max(y[i],y[j])/min(y[i],y[j])), 'difference_z':float(abs(y[i]-y[j])/math.hypot(rows[i]['se'], rows[j]['se']))})
    result['largest_feature_collision'] = max(collisions,key=lambda c:c['ratio']) if collisions else None
    if result['largest_feature_collision']:
        ids = result['largest_feature_collision']['ids']
        if all(rows[i]['n'] <= 10 for i in ids):
            result['largest_feature_collision']['exact_means'] = [float(exact_cover(graph_objects[i])) for i in ids]
    assert result['validation']['max_abs_z'] < 5, 'Simulation failed independent checks'
    (OUT/'validation.json').write_text(json.dumps(validations,indent=2))
    predrows=[]
    for p in preds:
        for i in np.where(masks[p])[0]:
            predrows.append(dict(protocol=p, id=int(i), family=rows[i]['family'], n=rows[i]['n'], observed=y[i], **{m:float(v[i]) for m,v in preds[p].items()}))
    with (OUT/'predictions.csv').open('w') as fh:
        wr=csv.DictWriter(fh,fieldnames=list(predrows[0])); wr.writeheader(); wr.writerows(predrows)
    plt.rcParams.update({'font.size':9})
    fig, axes = plt.subplots(1,2,figsize=(7.0,2.55), constrained_layout=True)
    colors=plt.get_cmap('tab10')
    for k,f in enumerate(FAMILIES):
        idx = masks['interpolation'] & np.array([r['family']==f for r in rows])
        axes[0].errorbar(y[idx], preds['interpolation']['four_stats'][idx], xerr=1.96*np.array([r['se'] for r in rows])[idx], fmt='o', ms=3, color=colors(k), label=f)
    axes[0].plot([5,10000],[5,10000], 'k--',lw=.8)
    axes[0].set(xscale='log',yscale='log',xlabel='Monte Carlo mean (steps)',ylabel='Four-statistic prediction',title='Held-out sizes 14 and 26')
    axes[0].legend(fontsize=6,ncol=3,loc='upper left')
    vals=[result['leave_family_out']['four_stats']['family_mape'][f] for f in FAMILIES]
    cis=np.array([result['leave_family_out']['four_stats']['family_mc95'][f] for f in FAMILIES])
    axes[1].bar(np.arange(9),vals,color=[colors(k) for k in range(9)])
    axes[1].errorbar(np.arange(9),vals,yerr=np.maximum(0,np.array([np.array(vals)-cis[:,0],cis[:,1]-np.array(vals)])),fmt='none',ecolor='black',capsize=2,lw=.8)
    axes[1].set(xticks=np.arange(9),xticklabels=FAMILIES,ylabel='Mean absolute percentage error',title='Leave one family out')
    axes[1].tick_params(axis='x',labelrotation=50,labelsize=7)
    fig.savefig(OUT/'results.pdf'); fig.savefig(OUT/'results.png',dpi=180); plt.close(fig)
    result['timing']={'simulation_and_validation_seconds':sim_seconds, 'total_seconds':time.perf_counter()-started}
    (OUT/'summary.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__ == '__main__': main()
