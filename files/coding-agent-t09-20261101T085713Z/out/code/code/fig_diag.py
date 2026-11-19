from analysis_common import *
from scipy.stats import spearmanr
names = ['e1_var', 'e2_main', 'e3_design', 'e4_scale', 'e5_dosenoise', 'e6_degree', 'e8_misspec_graph', 'e9_prob', 'e10_clusterres']
rows = []
for nm in names:
    df = load(nm)
    df = df[df.est.str.startswith('OLS')]
    if 'sigma' not in df: df['sigma'] = 1.0
    df['sigma'] = df.sigma.fillna(1.0)
    for k, g in df.groupby(['cid', 'est']):
        rows.append(dict(exp=nm, cid=k[0], est=k[1], mech=g.mech.iloc[0], design=g.design_kind.iloc[0], sigma=g.sigma.iloc[0],
                         sdN=g.errN.std(), w2=g.w2.mean(), w1=g.w1.mean(), biasS=g.errS.mean(), sdS=g.errS.std(), R=len(g),
                         bias_se=g.errS.std() / np.sqrt(len(g)), n=g.n.iloc[0], obs=g.get('obs_noise', pd.Series([0])).iloc[0]))
D = pd.DataFrame(rows); D['pred'] = D.sigma * D.w2; D['ratio'] = D.sdN / D.pred
D.to_csv(f'{RES}/summary_diag.csv', index=False)
print('N groups', len(D), ' sdN/pred ratio: median %.3f, 5-95%% [%.3f, %.3f]' % (D.ratio.median(), D.ratio.quantile(.05), D.ratio.quantile(.95)))
print('log-log corr', np.corrcoef(np.log(D.sdN), np.log(D.pred))[0, 1])
D0 = D[D.obs == 0]
fig, axs = plt.subplots(2, 1, figsize=(3.6, 2.8))
axs[0].loglog(D.pred, D.sdN, '.', ms=2, color=OI['OLS-x'], alpha=.5)
lim = [D.pred.min() * .8, D.pred.max() * 1.2]; axs[0].plot(lim, lim, 'k:', lw=.8)
axs[0].set_xlabel(r'predicted $\sigma\|w\|_2$'); axs[0].set_ylabel('empirical SD of noise term')
# bias vs w1 for linear-in-x estimators under smooth nonlinear mechanisms
cm = {'sat': '#D55E00', 'thresh': '#0072B2', 'quad': '#009E73', 'linfrac': '#999999', 'hetero': '#CC79A7', 'twohop': '#E69F00', 'peer': '#000000', 'lincount': '#56B4E9'}
q = D0[D0.est == 'OLS-x']
for m, g in q.groupby('mech'):
    axs[1].plot(g.w1, g.biasS.abs(), '.', ms=3, color=cm.get(m, 'k'), label=m)
axs[1].set_xlabel(r'$\|w\|_1$ (OLS-x)'); axs[1].set_ylabel('|bias| (noiseless fit)'); axs[1].legend(frameon=False, fontsize=5, ncol=2)
plt.tight_layout(); save('fig_diag')
for m, g in q.groupby('mech'):
    print(m, len(g), 'spearman(w1,|bias|)=%.2f' % spearmanr(g.w1, g.biasS.abs())[0])
