from analysis_common import *
df = load('e8_misspec_graph')
S = summarize(df, ['mech', 'obs_noise', 'design_kind', 'est'])
S.to_csv(f'{RES}/summary_e8.csv', index=False)
ests = ['DM', 'OLS-x', 'OLS-xd', 'OLS-x2', 'OLS-oracle']
fig, axs = plt.subplots(2, 3, figsize=(5.0, 2.8), sharex=True)
for j, m in enumerate(['linfrac', 'twohop', 'sat']):
    for e in ests:
        for dk, ls, row in [('bern', '-', 0), ('cluster', '--', 1)]:
            q = S[(S.mech == m) & (S.est == e) & (S.design_kind == dk)].sort_values('obs_noise')
            axs[row, j].plot(q.obs_noise, q.rmse, ls, marker='o', ms=2.5, color=OI[e], label=e if (j == 0 and row == 0) else None)
    
    axs[0, j].set_title(m)
    axs[1, j].set_xlabel('fraction of edges corrupted')
axs[0, 0].set_ylabel('RMSE (Bernoulli)'); axs[1, 0].set_ylabel('RMSE (cluster)')
axs[0, 0].legend(frameon=False, fontsize=5.5)
for a in axs.ravel(): a.set_yscale('log')
plt.tight_layout(); save('fig_e8')
print(S[(S.est.isin(['OLS-x', 'OLS-oracle', 'DM']))].pivot_table(index=['mech', 'design_kind', 'est'], columns='obs_noise', values=['bias', 'rmse']).round(2).to_string())
