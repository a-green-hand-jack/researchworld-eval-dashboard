from analysis_common import *
from gate import graphs as G
df = load('e9_prob')
df['p'] = df.design_p
S = summarize(df, ['graph', 'mech', 'p', 'est'])
S.to_csv(f'{RES}/summary_e9.csv', index=False)
mechs = ['linfrac', 'sat', 'thresh']
fig, axs = plt.subplots(2, 3, figsize=(7, 2.7), sharex=True)
gsel = 'sbm:n=3000,K=30,d=16,mix=0.1'
degs = np.asarray(G.make_graph(gsel).sum(1)).ravel()
pp = np.linspace(0.05, 0.5, 40)
for j, m in enumerate(mechs):
    for e in ['OLS-x', 'OLS-quad', 'OLS-oracle', 'GBDT']:
        q = S[(S.graph == gsel) & (S.mech == m) & (S.est == e)].sort_values('p')
        axs[0, j].plot(q.p, q.bias, marker='o', ms=3, color=OI[e], label=e)
        axs[1, j].plot(q.p, q.rmse, marker='o', ms=3, color=OI[e])
    axs[0, j].plot(pp, [slope_pred(m, p, degs) for p in pp], 'k:', lw=1, label='theory (OLS-x)')
    axs[0, j].axhline(0, color='k', lw=.4)
    axs[0, j].set_title(m); axs[1, j].set_yscale('log'); axs[1, j].set_xlabel('treatment probability $p$')
[plain_log(axs[1, j], [0.3, 0.5, 1, 2, 5]) for j in range(2)]; plain_log(axs[1, 2], [0.3, 1, 3, 10, 20])
axs[0, 0].set_ylabel('bias'); axs[1, 0].set_ylabel('RMSE'); axs[0, 1].legend(frameon=False, fontsize=5.5)
axs[0, 0].set_ylim(-1.5, 1.5); axs[0, 1].set_ylim(-1.5, 1.5); axs[0, 2].set_ylim(-1.5, 1.5)
plt.tight_layout(); save('fig_e9')
print(S[S.est == 'Hajek'].groupby(['graph', 'p']).fail.mean().round(2).unstack())
