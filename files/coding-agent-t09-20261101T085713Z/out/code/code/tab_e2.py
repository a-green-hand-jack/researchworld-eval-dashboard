from analysis_common import *
S = pd.read_csv(f'{RES}/summary_e2.csv'); S['rel'] = S.rmse / S.tau.abs()
graphs = ['ER', 'BA', 'WS', 'SBM', 'egoFB', 'Stanford3']
ests = ['DM', 'OLS-x', 'OLS-quad', 'OLS-oracle', 'GBDT', 'Hajek']
lines = []
for g in graphs:
    for d in ['bern', 'cluster']:
        q = S[(S.gshort == g) & (S.design_kind == d)]
        cut = q.cut.dropna().mean(); K = q.K.mean()
        row = [g, 'Bern' if d == 'bern' else f'Clust ($K{{=}}{int(K)}$, cut {cut:.2f})']
        best = {e: q[q.est == e].rel.median() for e in ests}
        mn = min(best.values())
        for e in ests:
            r = q[q.est == e].rel
            s = f'{r.median():.2f} ({r.min():.2f}--{r.max():.2f})'
            row.append(('\\textbf{' + s + '}') if best[e] == mn else s)
        lines.append(' & '.join(row) + r' \\')
    lines.append(r'\midrule')
open(f'{TAB}/tab_e2.tex', 'w').write('\n'.join(lines[:-1]) + '\n')
print('\n'.join(lines))
