"""Tables for one matrix setting: error(k) curves with bootstrap CIs and the pre-declared primary comparisons.
python exp/analyze_main.py SETTING [--ks 3,8,20]  ->  results/SETTING/{curves,primary,fa_rank}.csv"""
import sys, os, json, glob, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
import analysis as A

ap = argparse.ArgumentParser(); ap.add_argument('setting'); ap.add_argument('--ks', default='3,8,20')
ap.add_argument('--dir', default='results'); a = ap.parse_args()
d = f"{a.dir}/{a.setting}"
df = A.load(d); pm = A.per_model(df)
cells = sorted(set(zip(pm.selector, pm.method)))
avail_k = sorted(pm.k.unique()); ks = [k for k in map(int, a.ks.split(',')) if k in avail_k]
out = []
for s, m in cells:
    for metric in [x for x in ('mse', 'mae_raw', 'spear', 'pw_acc') if x in pm.columns]:
        c = A.curve(pm, s, m, metric, rmse=(metric == 'mse'))
        c['selector'] = s; c['method'] = m; c['metric'] = metric; out.append(c)
cur = pd.concat(out); cur.to_csv(f"{d}/curves.csv", index=False)

FA = 'fa'
pairs = []
def add(tag, x, y, post=False):
    if x in cells and y in cells: pairs.append((tag, x, y, post))
add('P1 greedyA vs random', ('greedyA', FA), ('random', FA))
for o in ('cluster', 'pivqr', 'leverage', 'central'):          # 'covered' is P2 (setting B only), not repeated under P3
    add(f'P3 greedyA vs {o}', ('greedyA', FA), (o, FA))
add('P2 greedyA vs covered', ('greedyA', FA), ('covered', FA))
for me in ('ridge', 'knn', 'softimpute'):
    add(f'P5 FA vs {me} (greedyA)', ('greedyA', FA), ('greedyA', me))
add('P7 greedyAcomp vs greedyA', ('greedyAcomp', FA), ('greedyA', FA), True)
add('P7 greedyAcomp vs random', ('greedyAcomp', FA), ('random', FA), True)
add('P8 greedyGauss+gcov vs greedyA+fa', ('greedyGauss', 'gcov'), ('greedyA', FA), True)
add('P8 greedyGauss+gcov vs random+gcov', ('greedyGauss', 'gcov'), ('random', 'gcov'), True)
rows = []
for tag, x, y, post in pairs:
    t = A.paired(pm, x, y, 'mse', ks=ks); t['test'] = tag; t['post_pilot'] = post; rows.append(t)
if rows:
    P = pd.concat(rows, ignore_index=True)
    P['p_holm'] = A.holm(P.p.values)
    P.to_csv(f"{d}/primary.csv", index=False)
    pd.set_option('display.width', 200)
    print(P[['test', 'k', 'diff', 'rel', 'lo', 'hi', 'p_holm', 'n_models']].round(4).to_string())
info = []
for f in sorted(glob.glob(f"{d}/info_rep*.json")):
    info += json.load(open(f))
if info:
    pd.DataFrame([{k: v for k, v in i.items() if k not in ('rank_scores', 'eig')} for i in info]).to_csv(f"{d}/fa_rank.csv", index=False)
print('\nRMSE (std units), FA inference, selectors at k=', ks)
t = cur[(cur.metric == 'mse') & (cur.method.isin(['fa', 'gcov'])) & (cur.k.isin(ks))].pivot_table(index=['selector', 'method'], columns='k', values='est')
print(t.round(3).to_string())
