from analysis_common import *
from matplotlib.colors import LogNorm
df = load('e2_main')
df['gshort'] = df.graph.str.split(':').str[0].replace({'er': 'ER', 'ba': 'BA', 'ws': 'WS', 'sbm': 'SBM', 'egofb': 'egoFB', 'stanford3': 'Stanford3'})
S = summarize(df, ['gshort', 'mech', 'design_kind', 'est'])
S['rel'] = S.rmse / S.tau.abs()
S.to_csv(f'{RES}/summary_e2.csv', index=False)
mechs = ['linfrac', 'lincount', 'sat', 'quad', 'thresh', 'twohop', 'hetero', 'peer']
graphs = ['ER', 'BA', 'WS', 'SBM', 'egoFB', 'Stanford3']
rows = [(g, d) for g in graphs for d in ['bern', 'cluster']]


def panel(ax, est, col='rel', title=None, vmin=0.02, vmax=1.0):
    M = np.full((len(rows), len(mechs)), np.nan)
    for i, (g, d) in enumerate(rows):
        for j, m in enumerate(mechs):
            q = S[(S.gshort == g) & (S.design_kind == d) & (S.mech == m) & (S.est == est)]
            if len(q): M[i, j] = q[col].iloc[0]
    im = ax.imshow(M, norm=LogNorm(vmin=vmin, vmax=vmax), cmap='viridis_r', aspect='auto')
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if not np.isnan(M[i, j]): ax.text(j, i, f'{M[i,j]:.2f}', ha='center', va='center', fontsize=6,
                                              color='white' if M[i, j] > 0.15 else 'black')
    ax.set_xticks(range(len(mechs))); ax.set_xticklabels(mechs, rotation=60, ha='right')
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([f'{g} {"B" if d=="bern" else "C"}' for g, d in rows])
    ax.set_title(title or est)
    for k in range(1, len(graphs)): ax.axhline(2 * k - 0.5, color='w', lw=1)
    return im


def make(ests, fname, nr, nc, w, h):
    fig, axs = plt.subplots(nr, nc, figsize=(w, h), sharey=True)
    for ax, e in zip(np.atleast_1d(axs).ravel(), ests):
        im = panel(ax, e)
    fig.subplots_adjust(hspace=0.55)
    fig.colorbar(im, ax=axs, shrink=0.6, label='RMSE / |GATE|')
    save(fname)


make(['DM', 'OLS-x', 'GBDT'], 'fig_e2_main', 1, 3, 7, 3.6)
make(['OLS-xd', 'OLS-quad', 'OLS-rich', 'OLS-oracle', 'Hajek', 'OLS-x2'], 'fig_e2_app', 2, 3, 7.2, 7.0)
# failure rates for Hajek
print(S[S.est == 'Hajek'][['gshort', 'mech', 'design_kind', 'fail']].query('fail>0').to_string())
# summary: mean rel RMSE per estimator per design
print(S.groupby(['design_kind', 'est']).rel.agg(['mean', 'median']).round(3))
