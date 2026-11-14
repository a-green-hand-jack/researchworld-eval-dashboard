"""LaTeX tables for the paper from results/summary_*.csv (+ theory_*.csv, E5_ballots.csv)."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
R = '/work/results/'; T = '/work/paper/tables/'; os.makedirs(T, exist_ok=True)
DS = {'galaxies': 'Galaxies', 'forest': 'Forest', 'alphafold': 'AlphaFold', 'gene_expression': 'Gene expression', 'census_income': 'Census income',
      'census_healthcare': 'Census health ins.', 'census_education': 'Census education'}
def S(exp): return pd.read_csv(R + f'summary_{exp}.csv')
def pv(s, **kw):
    for k, v in kw.items(): s = s[s[k] == v]
    return s
def cov(x): return f'{100*x:.1f}'
def rat(r, se): return f'{r:.3f}'
def pm(r, se): return f'{r:.3f}$\\;{{\\scriptstyle\\pm{1.96*se:.3f}}}$'

def tab_real():
    s = S('E1a'); th = pd.read_csv(R + 'theory_E1.csv'); pop = pd.read_csv(R + 'theory_pop.csv', index_col=0)
    L = ['\\begin{tabular}{lrrr rrrr rrrr}', '\\toprule', ' & & & & \\multicolumn{4}{c}{coverage (\\%)} & \\multicolumn{4}{c}{width / PPI++ (unclipped)}\\\\',
         '\\cmidrule(lr){5-8}\\cmidrule(lr){9-12}', 'data set & corr & $\\hat\\beta$ & $s$ & classical & PPI & PPI++ & auto & classical & PPI & auto & bound\\\\', '\\midrule']
    for d, nm in DS.items():
        x = pv(s, dgp=f'{d}|id', n=500); t = th[(th.dataset == d) & (th.n == 500) & (th.N == 20000)].iloc[0]
        g = lambda m: x[x.method == m].iloc[0]
        L.append(f"{nm} & {pop.loc[d,'corr']:.2f} & {pop.loc[d,'slope']:.2f} & {100*pop.loc[d,'share_nl']:.1f}\\% & " + ' & '.join(cov(g(m).cover) for m in ['classical', 'ppi', 'ppipp_u', 'auto'])
                 + f" & {g('classical').ratio_u:.2f} & {g('ppi').ratio_u:.2f} & {pm(g('auto').ratio_u, g('auto').ratio_u_se)} & {t.r_eff_ppu:.3f}\\\\")
    L += ['\\bottomrule', '\\end{tabular}']; open(T + 'tab_real.tex', 'w').write('\n'.join(L))

def tab_distort():
    s = S('E2'); th = pd.read_csv(R + 'theory_E2.csv')
    L = ['\\begin{tabular}{l r rrrr rrr r}', '\\toprule', ' & & \\multicolumn{4}{c}{width / PPI++ (unclipped)} & \\multicolumn{3}{c}{coverage (\\%)} & \\\\', '\\cmidrule(lr){3-6}\\cmidrule(lr){7-9}',
         'predictor output & $s$ & PPI & iso & auto & bound & PPI++ & iso & auto & $\\lambda^{\\rm clip}$-PPI++\\\\', '\\midrule']
    for key in th.dataset.unique():
        d, tr = key.split('|'); x = pv(s, dgp=key, n=1000); t = th[(th.dataset == key) & (th.n == 1000)].iloc[0]; g = lambda m: x[x.method == m].iloc[0]
        L.append(f"{DS[d]}, {tr} & {100*t.share_nl:.0f}\\% & {g('ppi').ratio_u:.2f} & {pm(g('iso').ratio_u, g('iso').ratio_u_se)} & {pm(g('auto').ratio_u, g('auto').ratio_u_se)} & {t.r_eff_ppu:.3f} & "
                 + f"{cov(g('ppipp_u').cover)} & {cov(g('iso').cover)} & {cov(g('auto').cover)} & {g('ppipp').ratio_u:.2f}\\\\")
    L += ['\\bottomrule', '\\end{tabular}']; open(T + 'tab_distort.tex', 'w').write('\n'.join(L))

def tab_shift():
    s = S('E4'); s = s[~s.method.str.endswith('_t')]
    L = ['\\begin{tabular}{ll rrrrr}', '\\toprule', 'setting & $n$ & classical & PPI & PPI++ & lin & auto\\\\', '\\midrule']
    for key, nm in [('plankton2013|id', 'no shift (2013 only)'), ('plankton2013->2014|id', 'shift 2013$\\to$2014')]:
        for n in [100, 500, 2000, 10000]:
            x = pv(s, dgp=key, n=n); g = lambda m: x[x.method == m].iloc[0]
            L.append(f"{nm if n==100 else ''} & {n} & " + ' & '.join(f"{cov(g(m).cover)}" for m in ['classical', 'ppi', 'ppipp', 'lin', 'auto']) + '\\\\')
        L.append('\\midrule' if key.startswith('plankton2013|') else '')
    L += ['\\bottomrule', '\\end{tabular}']; open(T + 'tab_shift.tex', 'w').write('\n'.join([l for l in L if l]))

def tab_ballots():
    b = pd.read_csv(R + 'E5_ballots.csv'); nm = {'classical': 'classical', 'ppi': 'PPI', 'ppipp': 'PPI++ (ppi\\_py)', 'ppipp_u': 'PPI++ (unclipped)', 'lin': 'cross-fit linear', 'iso': 'cross-fit isotonic', 'bin10': 'cross-fit 10 bins', 'spl': 'cross-fit spline', 'auto': 'cross-fit auto'}
    L = ['\\begin{tabular}{lrrr}', '\\toprule', 'method & lower & upper & width\\\\', '\\midrule']
    for _, r in b.iterrows(): L.append(f"{nm[r.method]} & {r.lo:.4f} & {r.hi:.4f} & {r.width:.5f}\\\\")
    L += ['\\bottomrule', '\\end{tabular}']; open(T + 'tab_ballots.tex', 'w').write('\n'.join(L))

def tab_validity():
    rows = []
    for exp in ['E1a', 'E1b', 'E2', 'E3a', 'E3b', 'E3c', 'E3d', 'E4']:
        if not os.path.exists(R + f'summary_{exp}.csv'): continue
        s = S(exp); s = s[~s.method.str.endswith('_t')]
        if exp == 'E4': s = s[s.dgp.str.startswith('plankton2013|')]
        s = s.assign(exp=exp); rows.append(s)
    a = pd.concat(rows); a = a[a.n >= 100]
    a['under'] = a.cover_hi < 0.95; a['over'] = a.cover_lo > 0.95
    g = a.groupby('method').agg(cells=('cover', 'size'), mean=('cover', 'mean'), minc=('cover', 'min'), under=('under', 'sum'), over=('over', 'sum')).reindex(['classical', 'ppi', 'ppipp', 'ppipp_u', 'lin', 'iso', 'bin10', 'spl', 'auto'])
    nm = {'classical': 'classical', 'ppi': 'PPI', 'ppipp': 'PPI++ (ppi\\_py)', 'ppipp_u': 'PPI++ (unclipped)', 'lin': 'cross-fit linear', 'iso': 'cross-fit isotonic', 'bin10': 'cross-fit 10 bins', 'spl': 'cross-fit spline', 'auto': 'cross-fit auto'}
    L = ['\\begin{tabular}{lrrrrr}', '\\toprule', 'method & cells & mean cov. (\\%) & min cov. (\\%) & \\#cells sig.\\ below 95 & \\#cells sig.\\ above 95\\\\', '\\midrule']
    for m, r in g.iterrows(): L.append(f"{nm[m]} & {int(r.cells)} & {100*r['mean']:.2f} & {100*r.minc:.1f} & {int(r.under)} & {int(r.over)}\\\\")
    L += ['\\bottomrule', '\\end{tabular}']; open(T + 'tab_validity.tex', 'w').write('\n'.join(L)); print(g.round(4))

def tab_logit():
    from dgps import SynthLogit, asym_vars
    L = ['\\begin{tabular}{lrr rrrr rrr}', '\\toprule', 'logit scores & $n$ & $N$ & \\multicolumn{4}{c}{width / PPI++ (unclipped)} & \\multicolumn{3}{c}{coverage (\\%)}\\\\', '\\cmidrule(lr){4-7}\\cmidrule(lr){8-10}',
         ' & & & PPI & auto & iso & bound & PPI++ & iso & auto\\\\', '\\midrule']
    for exp, mu, sg in [('E3c', -1.0, 2.0), ('E3d', -1.0, 4.0)]:
        if not os.path.exists(R + f'summary_{exp}.csv'): continue
        s = S(exp); s = s[~s.method.str.endswith('_t')]; m = SynthLogit(mu, sg).moments(); sh = m['var_h'] / (m['sig2'] + m['var_h'])
        for n, N in [(50, 20000), (200, 20000), (500, 500), (500, 5000), (500, 20000), (500, 50000), (3000, 20000)]:
            x = pv(s, n=n, N=N); g = lambda k: x[x.method == k].iloc[0]; a = asym_vars(m, n, N)
            L.append(f"{'$s{=}%.2f$' % sh if (n, N) == (50, 20000) else ''} & {n} & {N} & {g('ppi').ratio_u:.2f} & {pm(g('auto').ratio_u, g('auto').ratio_u_se)} & {pm(g('iso').ratio_u, g('iso').ratio_u_se)} & {np.sqrt(a['eff']/a['ppipp']):.3f} & {cov(g('ppipp_u').cover)} & {cov(g('iso').cover)} & {cov(g('auto').cover)}\\\\")
        L.append('\\midrule')
    L[-1] = '\\bottomrule'; L += ['\\end{tabular}']; open(T + 'tab_logit.tex', 'w').write('\n'.join(L))

def tab_xgain():
    x = pd.read_csv(R + 'xgain.csv'); nm = {'census_income': 'Census income', 'census_healthcare': 'Census health ins.', 'census_education': 'Census education'}
    L = ['\\begin{tabular}{lrrrrr}', '\\toprule', 'data set & lin($f$) & GB($f$) & GB($X$) & GB($f,X$) & gain of $X$ over GB($f$)\\\\', '\\midrule']
    for _, r in x.iterrows(): L.append(f"{nm[r.dataset]} & {r['linear(f)']:.4f} & {r['f']:.4f} & {r['X']:.4f} & {r['f+X']:.4f} & {100*(1-r['f+X']/r['f']):.2f}\\%\\\\")
    L += ['\\bottomrule', '\\end{tabular}']; open(T + 'tab_xgain.tex', 'w').write('\n'.join(L))

def tab_app_real():
    s = S('E1a'); s = s[~s.method.str.endswith('_t')]; ns = [50, 100, 200, 500, 1000, 2000, 5000]
    L = ['\\begin{tabular}{l' + 'r' * len(ns) + '}', '\\toprule', ' & ' + ' & '.join(f'$n{{=}}{n}$' for n in ns) + '\\\\']
    for title, m, col, f in [('width of auto / width of PPI++ (unclipped)', 'auto', 'ratio_u', lambda v: f'{v:.3f}'), ('width of PPI ($\\lambda{=}1$) / width of PPI++ (unclipped)', 'ppi', 'ratio_u', lambda v: f'{v:.3f}'),
                             ('coverage (\\%) of auto', 'auto', 'cover', lambda v: f'{100*v:.1f}'), ('coverage (\\%) of PPI++ (unclipped)', 'ppipp_u', 'cover', lambda v: f'{100*v:.1f}')]:
        L += ['\\midrule', f'\\multicolumn{{{len(ns)+1}}}{{l}}{{\\emph{{{title}}}}}\\\\']
        for d, nmx in DS.items():
            L.append(nmx + ' & ' + ' & '.join(f(pv(s, dgp=f'{d}|id', n=n, method=m).iloc[0][col]) for n in ns) + '\\\\')
    L += ['\\bottomrule', '\\end{tabular}']; open(T + 'tab_app_real.tex', 'w').write('\n'.join(L))

def tab_app_N():
    s = S('E1b'); s = s[~s.method.str.endswith('_t')]; Ns = [50, 250, 1000, 5000, 50000]
    L = ['\\begin{tabular}{l' + 'r' * len(Ns) + '}', '\\toprule', ' & ' + ' & '.join(f'$N{{=}}{n}$' for n in Ns) + '\\\\']
    for title, m, col, f in [('width of auto / width of PPI++ (unclipped), $n=500$', 'auto', 'ratio_u', lambda v: f'{v:.3f}'), ('width of PPI ($\\lambda{=}1$) / width of PPI++ (unclipped)', 'ppi', 'ratio_u', lambda v: f'{v:.3f}'),
                             ('width of classical / width of PPI++ (unclipped)', 'classical', 'ratio_u', lambda v: f'{v:.3f}'), ('coverage (\\%) of auto', 'auto', 'cover', lambda v: f'{100*v:.1f}')]:
        L += ['\\midrule', f'\\multicolumn{{{len(Ns)+1}}}{{l}}{{\\emph{{{title}}}}}\\\\']
        for d, nmx in DS.items():
            L.append(nmx + ' & ' + ' & '.join(f(pv(s, dgp=f'{d}|id', N=n, method=m).iloc[0][col]) for n in Ns) + '\\\\')
    L += ['\\bottomrule', '\\end{tabular}']; open(T + 'tab_app_N.tex', 'w').write('\n'.join(L))

if __name__ == '__main__':
    import sys
    for w in (sys.argv[1:] or ['real', 'distort', 'shift', 'ballots', 'validity', 'logit', 'xgain', 'app_real', 'app_N']): globals()['tab_' + w]()
