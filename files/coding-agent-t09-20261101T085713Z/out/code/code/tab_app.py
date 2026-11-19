from analysis_common import *
# E10 table (mechanism sat, thresh): RMSE per estimator by clustering resolution
S = pd.read_csv(f'{RES}/summary_e10.csv')
gname = {'egofb': 'egoFB', 'stanford3': 'Stanford3', 'ws:n=3000,k=16,b=0.1': 'WS', 'sbm:n=3000,K=30,d=16,mix=0.3': 'SBM(0.3)'}
lines = []
for g in gname:
    for r in sorted(S[S.graph == g].design_res.unique()):
        row = [gname[g], str(int(r))]
        q = S[(S.graph == g) & (S.design_res == r) & (S.mech == 'sat')]
        row += [f"{int(q.K.iloc[0])}", f"{q.cut.iloc[0]:.2f}"]
        for m in ['sat', 'thresh']:
            q = S[(S.graph == g) & (S.design_res == r) & (S.mech == m)]
            for e in ['DM', 'OLS-x', 'OLS-oracle', 'GBDT']:
                row.append(f"{q[q.est == e].rmse.iloc[0]:.2f}")
        lines.append(' & '.join(row) + r' \\')
    lines.append(r'\midrule')
open(f'{TAB}/tab_e10.tex', 'w').write('\n'.join(lines[:-1]) + '\n')
# E11 table
df = load('e11_homophily'); df['g'] = df.graph.str.split(':').str[0]
S = summarize(df, ['g', 'mech', 'comm_sd', 'design_kind', 'est']); S.to_csv(f'{RES}/summary_e11.csv', index=False)
lines = []
for g in ['sbm', 'ws', 'egofb']:
    for d in ['bern', 'cluster']:
        for e in ['DM', 'OLS-x', 'OLS-oracle']:
            q = S[(S.g == g) & (S.design_kind == d) & (S.mech == 'sat') & (S.est == e)].sort_values('comm_sd')
            lines.append(f"{ {'sbm':'SBM','ws':'WS','egofb':'egoFB'}[g] } & {'Bern' if d=='bern' else 'Clust'} & {e} & " + ' & '.join(f'{v:.2f}' for v in q.rmse) + r' \\')
    lines.append(r'\midrule')
open(f'{TAB}/tab_e11.tex', 'w').write('\n'.join(lines[:-1]) + '\n')
