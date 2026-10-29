"""Re-render of the supplied figures/foret_ablation.jpg (/initial-state/inputs/5).
All values are the numbers printed on the supplied figure (absolute scores, %).
Relative improvement is recomputed from them. Rethinking ratios are NOT printed
in the supplied figure; they are read off its line plot (approximate, +-2 points)
and marked as such. 'bound' = forced rethinking applied to every sample, a sample
counts if the rethought answer is correct (upper bound, cf. force_all_wait in the code).
"""
import os, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
bench = ['MathVision', 'MathVista', 'MathVerse', 'MMMU-Pro']
base   = np.array([29.75, 72.35, 53.13, 40.94])   # VL-Reasoner-7B in the supplied figure (matches the 'w/o Forced Rethinking' row of the ablation table)
forced = np.array([30.49, 72.90, 53.56, 41.15])   # base + forced rethinking on every sample
rethk  = np.array([32.27, 74.90, 54.19, 41.69])   # VL-Rethinker-7B (selective rethinking)
bound  = np.array([33.68, 76.00, 55.14, 42.51])   # upper bound
ratio  = np.array([36, 24, 78, 18])               # % of responses with rethinking, read from the supplied plot
rel = lambda x: 100 * (x / base - 1)
series = [('Forced (trigger at test time)', forced, '#0072B2'), ('VL-Rethinker-7B (selective)', rethk, '#D55E00'),
          ('Bound', bound, '#999999')]
plt.rcParams.update({'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False})
fig, (a, b) = plt.subplots(1, 2, figsize=(5.8, 2.5), gridspec_kw={'width_ratios': [3, 1.1], 'wspace': 0.5})
x = np.arange(4); w = 0.26
for i, (n, v, c) in enumerate(series):
    bars = a.bar(x + (i - 1) * w, rel(v), w, color=c, label=n)
    for xx, r in zip(x + (i - 1) * w, rel(v)):
        a.text(xx, r + 0.2, f'{r:.1f}', ha='center', va='bottom', fontsize=6.5)
a.set_xticks(x); a.set_xticklabels([f'{n}\n({s:.2f})' for n, s in zip(bench, base)])
a.tick_params(axis='x', labelsize=7); b.tick_params(axis='y', labelsize=7); a.set_ylabel('Relative improvement\nover VL-Reasoner-7B (%)'); a.set_ylim(0, 15)
a.yaxis.grid(True, ls=':', c='0.8'); a.set_axisbelow(True)
a.legend(frameon=False, fontsize=6.5, loc='upper right')
a.set_title('(a) Gain over VL-Reasoner-7B', fontsize=8, loc='left')
b.barh(x[::-1], ratio, color='#D55E00', alpha=.75, height=.55)
for xx, r in zip(x[::-1], ratio): b.text(r + 2, xx, f'$\\approx${r}', va='center', fontsize=7)
b.set_yticks(x[::-1]); b.set_yticklabels(bench); b.set_xlim(0, 100)
b.set_xlabel('Rethinking ratio (%)'); b.xaxis.grid(True, ls=':', c='0.8'); b.set_axisbelow(True)
b.set_title('(b) Rethinking ratio\nof VL-Rethinker-7B', fontsize=8, loc='left')
fig.savefig(os.path.join(OUT, 'figures', 'foret_ablation.pdf'), bbox_inches='tight')
fig.savefig(os.path.join('/tmp', 'foret_preview.png'), bbox_inches='tight', dpi=200)
