"""Prints the key numbers quoted in the paper text (so every quoted number can be traced to results/)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
from dgps import SynthQuad, SynthLogit, asym_vars
R = '/work/results/'
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300)
def S(e): s = pd.read_csv(R + f'summary_{e}.csv'); return s
s = S('E3a'); s['c'] = s.dgp.str.extract(r'c=([0-9.]+)')[0].astype(float)
rows = []
for _, r in s[s.method.isin(['auto', 'spl', 'iso', 'lin'])].iterrows():
    a = asym_vars(SynthQuad(1, r.c, 1).moments(), int(r.n), int(r.N)); rows.append(dict(c=r.c, N=r.N, method=r.method, emp=r.ratio_u, theory=np.sqrt(a['eff'] / a['ppipp']), diff=r.ratio_u - np.sqrt(a['eff'] / a['ppipp'])))
d = pd.DataFrame(rows); print('E3a: emp-theory diff (auto/spl) summary'); print(d[d.method.isin(['auto', 'spl'])].groupby('method')['diff'].describe().round(4))
print(d[(d.method == 'auto')].pivot_table(index='c', columns='N', values='emp').round(3)); print(d[(d.method == 'auto')].pivot_table(index='c', columns='N', values='theory').round(3))
for e in ['E3c', 'E3d']:
    try: s = S(e)
    except Exception: continue
    mu, sg = (-1.0, 2.0) if e == 'E3c' else (-1.0, 4.0); m = SynthLogit(mu, sg).moments()
    s = s[~s.method.str.endswith('_t')]
    print(e, 'share s=', m['var_h'] / (m['sig2'] + m['var_h']))
    p = s.pivot_table(index=['n', 'N'], columns='method', values='ratio_u')[['classical', 'ppi', 'lin', 'iso', 'bin10', 'spl', 'auto']].round(3)
    p['theory'] = [np.sqrt(asym_vars(m, n, N)['eff'] / asym_vars(m, n, N)['ppipp']) for n, N in p.index]; print(p.round(3))
    print(s.pivot_table(index=['n', 'N'], columns='method', values='cover')[['classical', 'ppi', 'ppipp_u', 'lin', 'iso', 'auto']].round(3))
