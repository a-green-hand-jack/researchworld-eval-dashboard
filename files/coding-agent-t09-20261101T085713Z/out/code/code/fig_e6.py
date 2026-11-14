from analysis_common import *
from gate import graphs as G
df = load('e6_degree')
df['dk'] = df.design_kind
S = summarize(df, ['graph', 'mech', 'dk', 'est'])
S.to_csv(f'{RES}/summary_e6.csv', index=False)
mechs = ['linfrac', 'sat', 'thresh', 'quad']
cols = {'bern': '#0072B2', 'cluster': '#D55E00', 'sat': '#009E73'}
fig, axs = plt.subplots(2, 4, figsize=(7.2, 2.7), sharex=True)
degs = {}
for j, m in enumerate(mechs):
    q0 = S[(S.mech == m) & (S.est == 'OLS-x')]
    for dk in ['bern', 'cluster', 'sat']:
        q = q0[q0.dk == dk].sort_values('dbar')
        axs[0, j].errorbar(q.dbar, q.biasS, yerr=1.96 * q.sdS / np.sqrt(q.R), marker='o', ms=3, color=cols[dk], label={'bern': 'Bernoulli', 'cluster': 'cluster', 'sat': 'rand. sat.'}[dk], lw=1, capsize=1.5)
        axs[1, j].plot(q.dbar, q.rmse, marker='o', ms=3, color=cols[dk])
    # theory for Bernoulli p=.5 using actual degree sequences
    q = q0[q0.dk == 'bern'].sort_values('dbar')
    th = []
    for gname in q.graph:
        A = G.make_graph(gname); th.append(slope_pred(m, 0.5, np.asarray(A.sum(1)).ravel()))
    axs[0, j].plot(q.dbar, th, 'k:', lw=1, label='theory (Prop. 2)')
    axs[0, j].axhline(slope_limit(m, 0.5), color='gray', lw=.6, ls='--')
    axs[0, j].axhline(0, color='k', lw=.4)
    axs[0, j].set_title(m); axs[0, j].set_xscale('log'); axs[1, j].set_xscale('log'); axs[1, j].set_yscale('log')
    axs[1, j].set_xlabel('mean degree $d$')
[plain_log(axs[1, j], [0.2, 0.5, 1, 2]) for j in range(4)]
axs[0, 0].set_ylabel('bias (noiseless fit)'); axs[1, 0].set_ylabel('RMSE (OLS-x)')
axs[0, 0].legend(frameon=False, fontsize=5, loc='upper left')
plt.tight_layout(); save('fig_e6')
# estimator comparison vs d under Bern on sat
t = S[(S.mech == 'sat') & (S.dk == 'bern')].pivot_table(index='dbar', columns='est', values='rmse')
print(t.round(2))
