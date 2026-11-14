from analysis_common import *
from gate import graphs as G
# Prop. 2 check on e9 (p sweep) and e6 (degree sweep): empirical noiseless bias of OLS-x vs predicted
out = []
df = load('e9_prob'); df = df[df.est == 'OLS-x']
for (gname, m, p), g in df.groupby(['graph', 'mech', 'design_p']):
    if m == 'hetero': continue
    degs = np.asarray(G.make_graph(gname).sum(1)).ravel()
    pr = slope_pred(m, p, degs)
    out.append(dict(exp='e9', graph=gname, mech=m, p=p, d=degs.mean(), emp=g.errS.mean(), se=g.errS.std() / np.sqrt(len(g)), pred=pr))
try:
    df = load('e6_degree'); df = df[(df.est == 'OLS-x') & (df.design_kind == 'bern')]
    for (gname, m), g in df.groupby(['graph', 'mech']):
        if m == 'hetero': continue
        degs = np.asarray(G.make_graph(gname).sum(1)).ravel()
        out.append(dict(exp='e6', graph=gname, mech=m, p=0.5, d=degs.mean(), emp=g.errS.mean(), se=g.errS.std() / np.sqrt(len(g)), pred=slope_pred(m, 0.5, degs)))
except FileNotFoundError: pass
T = pd.DataFrame(out); T['diff'] = T.emp - T.pred; T['z'] = T['diff'] / T.se
T.to_csv(f'{RES}/summary_theory.csv', index=False)
pd.set_option('display.width', 200)
print(T.round(3).to_string())
for e, g in T.groupby('exp'):
    print(e, 'corr(emp,pred)=%.3f' % np.corrcoef(g.emp, g.pred)[0, 1], 'mean|diff|=%.3f' % g['diff'].abs().mean(), 'max|diff|=%.3f' % g['diff'].abs().max())
