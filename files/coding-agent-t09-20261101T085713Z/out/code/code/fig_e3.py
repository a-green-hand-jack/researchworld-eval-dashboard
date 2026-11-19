from analysis_common import *
df = load('e3_design')
df['dk'] = df.design_kind + df.design_p.fillna(0).astype(str)
df.loc[df.design_kind == 'sat', 'dk'] = 'sat'
S = summarize(df, ['graph', 'mech', 'dk', 'est'])
S['mix'] = S.graph.str.extract(r'mix=([\d.]+)').astype(float)
S['rel'] = S.rmse / S.tau.abs(); S['rel_lo'] = S.rmse_lo / S.tau.abs(); S['rel_hi'] = S.rmse_hi / S.tau.abs()
S.to_csv(f'{RES}/summary_e3.csv', index=False)
names = {'bern0.5': 'Bernoulli $p{=}.5$', 'bern0.2': 'Bernoulli $p{=}.2$', 'cluster0.5': 'cluster', 'sat': 'rand. saturation'}
cols = {'bern0.5': '#0072B2', 'bern0.2': '#56B4E9', 'cluster0.5': '#D55E00', 'sat': '#009E73'}
ests = ['DM', 'OLS-x', 'OLS-oracle', 'GBDT']
mechs = ['sat', 'thresh']
fig, axs = plt.subplots(len(mechs), len(ests), figsize=(7, 2.7), sharex=True, sharey=True)
for i, m in enumerate(mechs):
    for j, e in enumerate(ests):
        ax = axs[i, j]
        for dk in names:
            q = S[(S.mech == m) & (S.est == e) & (S.dk == dk)].sort_values('mix')
            ax.errorbar(q.mix, q.rel, yerr=[q.rel - q.rel_lo, q.rel_hi - q.rel], marker='o', ms=3, color=cols[dk], label=names[dk], capsize=1.5, lw=1)
        ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xticks([0.02, 0.1, 0.3, 0.6]); ax.set_xticklabels(['.02', '.1', '.3', '.6']); ax.minorticks_off()
        if i == 0: ax.set_title(e)
        if j == 0: ax.set_ylabel(f'{m}\nRMSE/|GATE|')
        if i == len(mechs) - 1: ax.set_xlabel('between-block edge share')
axs[0, 0].legend(frameon=False, fontsize=5.5)
plt.tight_layout(); save('fig_e3')
# decomposition table at mix=0.1
rows = []
for m in ['sat', 'thresh', 'hetero']:
    for dk in names:
        q = S[(S.mech == m) & (S.est == 'OLS-x') & (S.dk == dk) & (S.mix == 0.1)].iloc[0]
        rows.append(f"{m} & {names[dk]} & {q.bias:+.2f} & {q.sdS:.2f} & {q.sdN:.2f} & {q.rmse:.2f} & {q.w1:.1f} & {q.w2:.3f} \\\\")
open(f'{TAB}/tab_e3.tex', 'w').write('\n'.join(rows) + '\n'); print('\n'.join(rows))
# Hajek failure rates
print(S[(S.est == 'Hajek') & (S.fail > 0)][['mech', 'dk', 'mix', 'fail']].groupby(['dk']).fail.agg(['mean', 'max', 'count']))
