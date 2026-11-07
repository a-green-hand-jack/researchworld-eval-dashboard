"""Render LaTeX tables (tables/*.tex) from the csv/json produced by fig_e*.py."""
import json, sys, numpy as np, pandas as pd
T = '/work/tables/'
th = lambda x: f'{int(x):,}'.replace(',', r'\,')
def fmt_t(x, cap=30000):
    return r'$>$30k' if not np.isfinite(x) else th(x)
def wrap(name, cols, header, rows):
    with open(T + name + '_tab.tex', 'w') as f:
        f.write('\\begin{tabular}{' + cols + '}\n\\toprule\n' + header + ' \\\\\n\\midrule\n' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}\n')
# ---- E1
df = pd.read_csv(T + 'e1_table.csv')
L = []
for _, r in df.iterrows():
    ci = lambda lo, hi: '' if not (np.isfinite(lo) and np.isfinite(hi)) else ' [' + th(lo) + ', ' + th(hi) + ']'
    L.append(f"{int(r.width)} & {th(r.P)} & {int(round(r.fit*8))}/{int(round(r.gen*8))} & {fmt_t(r.t_fit)} & {fmt_t(r.t_gen)}{ci(r.t_gen_lo, r.t_gen_hi)} & {r.va_fit:.2f} & {int(round(r.mem_first*8))} & {r.norm_gen:.1f} \\\\")
wrap('e1', 'rrcrrccc', r'$d$ & $P$ & fit/gen & $t_{\mathrm{fit}}$ & $t_{\mathrm{gen}}$ [95\% CI] & $a^{\mathrm{val}}_{\mathrm{fit}}$ & mem. & $\|\theta\|_{\mathrm{gen}}$', L)
# ---- E2
df = pd.read_csv(T + 'e2_table.csv')
L = []
for _, r in df.iterrows():
    L.append(f"{int(r.width)} & {r.lr:.0e} & {r.wd:g} & {r.lr*r.wd:.1e} & {int(r.gen)}/{int(r.n)} & {fmt_t(r.t_fit)} & {fmt_t(r.t_gen) if np.isfinite(r.t_gen) else '--'} & {('%.1f' % r.clock) if np.isfinite(r.clock) else '--'} & {('%.1f' % r.norm_gen) if np.isfinite(r.norm_gen) else '--'} \\\\")
wrap('e2', 'rrrrcrrrr', r'$d$ & lr & wd & lr$\cdot$wd & gen & $t_{\mathrm{fit}}$ & $t_{\mathrm{gen}}$ & clock & $\|\theta\|_{\mathrm{gen}}$', L)
# ---- E5
df = pd.read_csv(T + 'e5_table.csv')
L = []
for _, r in df.iterrows():
    L.append(f"{int(r.width)} & {r.c:.1f} & {int(r.gen)}/{int(r.n)} & {fmt_t(r.t_fit)} & {fmt_t(r.t_gen) if np.isfinite(r.t_gen) else '--'} & {fmt_t(r.delay) if np.isfinite(r.delay) else '--'} & {('%.1f' % r.norm_gen) if np.isfinite(r.norm_gen) else '--'} \\\\")
wrap('e5', 'rcrrrrr', r'$d$ & $c$ & gen & $t_{\mathrm{fit}}$ & $t_{\mathrm{gen}}$ & delay & $\|\theta\|_{\mathrm{gen}}$', L)
print('ok')
