from analysis_common import *
T = pd.read_csv(f'{RES}/summary_theory.csv')
q = T[(T.exp == 'e9') & T.graph.str.startswith('sbm')].sort_values(['mech', 'p'])
lines = [f"{r.mech} & {r.p:.2f} & {r.emp:+.3f} & {r.se:.3f} & {r.pred:+.3f} & {r['diff']:+.3f} \\\\" for _, r in q.iterrows()]
open(f'{TAB}/tab_theory.tex', 'w').write('\n'.join(lines) + '\n')
s = {e: dict(n=len(g), maxz=g.z.abs().max(), mad=g['diff'].abs().mean(), mx=g['diff'].abs().max(), corr=np.corrcoef(g.emp, g.pred)[0, 1]) for e, g in T.groupby('exp')}
print(s); print('all', len(T), T.z.abs().max(), (T.z.abs() > 1.96).sum())
