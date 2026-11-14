from analysis_common import *
df = load('e4_scale')
S = summarize(df, ['graph', 'n', 'mech', 'design_kind', 'est'])
S.to_csv(f'{RES}/summary_e4.csv', index=False)
ests = ['DM', 'OLS-x', 'OLS-oracle', 'GBDT']
mechs = ['linfrac', 'sat', 'thresh']
fig, axs = plt.subplots(2, 3, figsize=(7, 3.4), sharex=True)
for j, m in enumerate(mechs):
    for e in ests:
        for dk, ls in [('bern', '-'), ('cluster', '--')]:
            q = S[(S.mech == m) & (S.est == e) & (S.design_kind == dk)].sort_values('n')
            axs[0, j].plot(q.n, q.rmse, ls, marker='o', ms=2.5, color=OI[e], label=f'{e} {"B" if dk=="bern" else "C"}')
            axs[1, j].plot(q.n, q.bias.abs(), ls, marker='o', ms=2.5, color=OI[e])
    for i in range(2):
        axs[i, j].set_xscale('log'); axs[i, j].set_yscale('log')
    axs[0, j].set_title(m); axs[1, j].set_xlabel('$n$')
nn = np.array([1000, 16000]); axs[0, 1].plot(nn, 0.5 * np.sqrt(1000 / nn), 'k:', lw=.8)
axs[0, 0].set_ylabel('RMSE'); axs[1, 0].set_ylabel('|bias|')
axs[0, 0].legend(frameon=False, fontsize=4.5, ncol=2, loc='lower left')
plt.tight_layout(); save('fig_e4')
