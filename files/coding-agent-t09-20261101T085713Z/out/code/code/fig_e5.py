from analysis_common import *
df = load('e5_dosenoise')
S = summarize(df, ['mech', 'gamma', 'sigma', 'design_kind', 'est'])
S.to_csv(f'{RES}/summary_e5.csv', index=False)
ests = ['DM', 'OLS-x', 'OLS-oracle', 'GBDT']
fig, axs = plt.subplots(2, 4, figsize=(7.2, 3.4))
for i, m in enumerate(['linfrac', 'sat']):
    for k, (dk, ls) in enumerate([('bern', '-'), ('cluster', '--')]):
        for e in ests:
            q = S[(S.mech == m) & (S.sigma == 1.0) & (S.est == e) & (S.design_kind == dk)].sort_values('gamma')
            axs[i, 0].plot(q.gamma, q.bias.abs(), ls, marker='o', ms=2.5, color=OI[e], label=f'{e} {dk}' if i == 0 else None)
            axs[i, 1].plot(q.gamma, q.rmse, ls, marker='o', ms=2.5, color=OI[e])
            q = S[(S.mech == m) & (S.gamma == 1.0) & (S.est == e) & (S.design_kind == dk)].sort_values('sigma')
            axs[i, 2].plot(q.sigma, q.rmse, ls, marker='o', ms=2.5, color=OI[e])
            axs[i, 3].plot(q.sigma, q.bias.abs(), ls, marker='o', ms=2.5, color=OI[e])
    axs[i, 0].set_ylabel(m)
axs[1, 0].set_xlabel('interference strength $\\gamma$'); axs[1, 1].set_xlabel('$\\gamma$'); axs[1, 2].set_xlabel('noise $\\sigma$'); axs[1, 3].set_xlabel('$\\sigma$')
for t, a in zip(['|bias| vs $\\gamma$', 'RMSE vs $\\gamma$', 'RMSE vs $\\sigma$', '|bias| vs $\\sigma$'], axs[0]): a.set_title(t)
axs[0, 0].legend(frameon=False, fontsize=4.5, ncol=1)
for a in axs.ravel(): a.set_yscale('log')
plt.tight_layout(); save('fig_e5')
