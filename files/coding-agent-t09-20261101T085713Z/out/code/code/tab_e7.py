from analysis_common import *
df = load('e7_infer')
df = df[df.est == 'OLS-x'].copy()
rows = []
for k, g in df.groupby(['graph', 'mech', 'design_kind']):
    r = dict(graph=k[0].split(':')[0], mech=k[1], design=k[2], bias=g.err.mean(), rmse=np.sqrt((g.err ** 2).mean()), R=len(g))
    for se in ['se_iid', 'se_hc0', 'se_hc3', 'se_cl']:
        cov = (np.abs(g.err) <= 1.96 * g[se]).mean(); r['cov_' + se] = cov; r['ratio_' + se] = (g[se].mean() / g.err.std())
    rows.append(r)
T = pd.DataFrame(rows); T.to_csv(f'{RES}/summary_e7.csv', index=False)
pd.set_option('display.width', 250); print(T.round(3).to_string())

def fmt(T, mechs, path):
    lines = []
    for _, r in T[T.mech.isin(mechs)].iterrows():
        g = {'er': 'ER', 'sbm': 'SBM'}[r.graph]
        lines.append(f"{g} & {r.mech} & {'Bern' if r.design == 'bern' else 'Clust'} & {r.bias:+.2f} & {r.rmse:.2f} & {r.cov_se_iid:.2f} & {r.cov_se_hc3:.2f} & {r.cov_se_cl:.2f} & {r.ratio_se_iid:.2f} & {r.ratio_se_cl:.2f} \\\\")
    open(path, 'w').write('\n'.join(lines) + '\n')


fmt(T.sort_values(['graph', 'mech', 'design'], ascending=[False, True, True]), ['linfrac', 'sat'], f'{TAB}/tab_e7.tex')
fmt(T.sort_values(['graph', 'mech', 'design'], ascending=[False, True, True]), ['linfrac', 'sat', 'hetero', 'peer'], f'{TAB}/tab_e7_full.tex')
