from analysis_common import *
df = load('e1_var')
S = summarize(df, ['sweep', 'comm_sd', 'graph', 'est'])
S.to_csv(f'{RES}/summary_e1.csv', index=False)
fig, ax = plt.subplots(1, 3, figsize=(7, 2.2))
for cs, ls in [(0.0, '--'), (0.5, '-')]:
    d = S[(S.sweep == 'deg') & (S.comm_sd == cs)]
    for est in ['OLS-x', 'OLS-oracle']:
        q = d[d.est == est].sort_values('dbar')
        ax[0].plot(q.dbar, q.rmse, ls, marker='o', ms=3, color=OI[est], label=f'{est}, comm={cs}')
q = S[(S.sweep == 'deg') & (S.comm_sd == 0.5) & (S.est == 'DM')].sort_values('dbar')
ax[0].plot(q.dbar, q.rmse, '-', marker='o', ms=3, color=OI['DM'], label='DM')
ax[0].set_xscale('log'); ax[0].set_yscale('log'); ax[0].set_xlabel('mean degree $d$'); ax[0].set_ylabel('RMSE of GATE'); ax[0].legend(frameon=False, fontsize=5, loc='lower right')
ax[0].set_title('(a) RMSE vs degree ($n=3000$)')
# (b) noise-component SD vs predicted sigma*||w||_2
d = S[(S.est == 'OLS-x')]
ax[1].loglog([0.03, 0.6], [0.03, 0.6], 'k:', lw=0.8)
for sw, mk in [('deg', 'o'), ('n', 's')]:
    q = d[d.sweep == sw]
    ax[1].scatter(q.w2, q.sdN, marker=mk, s=14, color=OI['OLS-x'], label=f'{sw} sweep')
ax[1].minorticks_off(); ax[1].set_xticks([0.05, 0.1, 0.2, 0.4]); ax[1].set_xticklabels(['.05', '.1', '.2', '.4']); ax[1].set_yticks([0.05, 0.1, 0.2, 0.4]); ax[1].set_yticklabels(['.05', '.1', '.2', '.4']); ax[1].set_xlabel(r'predicted $\sigma\|w\|_2$'); ax[1].set_ylabel('empirical SD of noise component'); ax[1].legend(frameon=False)
ax[1].set_title('(b) noise term matches prediction')
# (c) n scaling
for cs, ls in [(0.0, '--'), (0.5, '-')]:
    d = S[(S.sweep == 'n') & (S.comm_sd == cs)]
    for est in ['OLS-x', 'DM']:
        q = d[d.est == est].sort_values('n')
        ax[2].plot(q.n, q.rmse, ls, marker='o', ms=3, color=OI[est])
nn = np.array([500, 16000]); ax[2].plot(nn, 0.36 * np.sqrt(1000 / nn) , 'k:', lw=0.8, label=r'$\propto n^{-1/2}$')
ax[2].set_xscale('log'); ax[2].set_yscale('log'); ax[2].set_xlabel('$n$ ($d=16$)'); ax[2].set_title('(c) RMSE vs $n$'); ax[2].legend(frameon=False)
plt.tight_layout(); save('fig_e1')
# table of ratio checks
t = S[(S.est == 'OLS-x')][['sweep', 'comm_sd', 'dbar', 'n', 'w1', 'w2', 'sdN', 'sdS', 'bias', 'rmse']]
print(t.round(3).to_string())
