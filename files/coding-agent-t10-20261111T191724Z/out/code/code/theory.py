"""Population-level (asymptotic) variance formulas evaluated on each real data set's empirical population.
 classical: Var(Y)/n          PPI (lam=1): Var(Y-f)/n + Var(f)/N
 PPI++ (lam* clipped to [0,1], as in ppi_py): Var(Y-lam f)/n + lam^2 Var(f)/N      lam* = Cov(Y,f)/Var(f) * N/(n+N)
 efficient given f only: E[Var(Y|f)]/n + Var(g)/(n+N),  g=E[Y|f] (estimated by 5-fold cross-validated isotonic regression)
 Also: Var(Y|f) residual share of the nonlinear part  s_h = (E[(Y-lin)^2] - E[(Y-g)^2]) / E[(Y-lin)^2].
Writes results/theory_pop.csv (one row per data set) and results/theory_E1.csv (per n,N)."""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import KFold
from cppi import _spl
from dgps import TRANSFORMS
D = '/work/data/'
REAL = ['galaxies', 'forest', 'alphafold', 'gene_expression', 'census_income', 'census_healthcare', 'census_education']

def cv_resid(f, y, fit, K=5, seed=0):
    pred = np.empty_like(y)
    for tr, te in KFold(K, shuffle=True, random_state=seed).split(f): pred[te] = fit(f[tr], y[tr])(f[te])
    return ((y - pred) ** 2).mean()

def iso(f, y): return IsotonicRegression(out_of_bounds='clip').fit(f, y).predict

def pop_moments(name, transform=None):
    d = np.load(D + name + '.npz'); y = d['Y'].astype(float); f = d['Yhat'].astype(float)
    if transform is not None: f = transform(f)
    Vy, V = y.var(), f.var(); c = np.cov(y, f, ddof=0)[0, 1]; b = c / V
    r_lin = Vy - c * c / V
    r_iso = cv_resid(f, y, iso); r_spl = cv_resid(f, y, _spl)
    r_np = min(r_iso, r_spl, r_lin)       # E[Var(Y|f)] upper-bound estimate (cross-validated), never above linear residual
    return dict(Vy=Vy, V=V, c=c, slope=b, corr=c / np.sqrt(Vy * V), r_lin=r_lin, r_iso_cv=r_iso, r_spl_cv=r_spl, r_np=r_np,
                Vid=((y - f) ** 2).mean() - (y.mean() - f.mean()) ** 2, share_nl=1 - r_np / r_lin, P=len(y))

def asym(m, n, N):
    M = n + N; lam = np.clip(m['c'] / m['V'] * N / M, 0, 1)
    v_cl = m['Vy'] / n
    v_ppi = m['Vid'] / n + m['V'] / N
    v_pp = (m['Vy'] - 2 * lam * m['c'] + lam ** 2 * m['V']) / n + lam ** 2 * m['V'] / N
    lu = m['c'] / m['V'] * N / M
    v_ppu = (m['Vy'] - 2 * lu * m['c'] + lu ** 2 * m['V']) / n + lu ** 2 * m['V'] / N
    v_eff = m['r_np'] / n + (m['Vy'] - m['r_np']) / M
    return dict(classical=v_cl, ppi=v_ppi, ppipp=v_pp, ppipp_u=v_ppu, eff=v_eff)

if __name__ == '__main__':
    pops = {}
    for nm in REAL: pops[nm] = pop_moments(nm)
    pd.DataFrame(pops).T.rename_axis('dataset').to_csv('/work/results/theory_pop.csv')
    rows = []
    for nm, m in pops.items():
        for n, N in [(n, 20000) for n in [50, 100, 200, 500, 1000, 2000, 5000]] + [(500, N) for N in [50, 250, 1000, 5000, 50000]]:
            v = asym(m, n, N)
            rows.append(dict(dataset=nm, n=n, N=N, **{f'w_{k}': np.sqrt(x) for k, x in v.items()},
                             r_eff_pp=np.sqrt(v['eff'] / v['ppipp']), r_ppi_pp=np.sqrt(v['ppi'] / v['ppipp']), r_cl_pp=np.sqrt(v['classical'] / v['ppipp']), r_eff_ppu=np.sqrt(v['eff'] / v['ppipp_u']), r_ppi_ppu=np.sqrt(v['ppi'] / v['ppipp_u']), r_cl_ppu=np.sqrt(v['classical'] / v['ppipp_u']), r_pp_ppu=np.sqrt(v['ppipp'] / v['ppipp_u'])))
    pd.DataFrame(rows).to_csv('/work/results/theory_E1.csv', index=False)
    rows = []
    for nm, tr in [('galaxies', 'logit'), ('galaxies', 'pow3'), ('alphafold', 'logit'), ('forest', 'logit'),
                   ('gene_expression', 'exp'), ('census_healthcare', 'logit'), ('census_income', 'sqrt')]:
        m = pop_moments(nm, TRANSFORMS[tr])
        for n in [100, 300, 1000, 3000]:
            v = asym(m, n, 20000)
            rows.append(dict(dataset=f'{nm}|{tr}', n=n, N=20000, share_nl=m['share_nl'], corr=m['corr'], **{f'w_{k}': np.sqrt(x) for k, x in v.items()},
                             r_eff_pp=np.sqrt(v['eff'] / v['ppipp']), r_ppi_pp=np.sqrt(v['ppi'] / v['ppipp']), r_cl_pp=np.sqrt(v['classical'] / v['ppipp']), r_eff_ppu=np.sqrt(v['eff'] / v['ppipp_u']), r_ppi_ppu=np.sqrt(v['ppi'] / v['ppipp_u']), r_cl_ppu=np.sqrt(v['classical'] / v['ppipp_u']), r_pp_ppu=np.sqrt(v['ppipp'] / v['ppipp_u'])))
    pd.DataFrame(rows).to_csv('/work/results/theory_E2.csv', index=False)
    print(pd.DataFrame(rows).query('n==1000')[['dataset','share_nl','corr','r_eff_pp','r_eff_ppu','r_ppi_ppu','r_cl_ppu','r_pp_ppu']].round(3))
    print(pd.DataFrame(pops).T[['corr', 'slope', 'r_lin', 'r_iso_cv', 'r_spl_cv', 'share_nl']].round(4))
