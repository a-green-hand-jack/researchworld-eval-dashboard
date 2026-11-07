"""E6: other operations. Writes tables/e6_table.csv and tables/e6_tab.tex"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
import ana
df = ana.load('/work/results/e6_ops')
d1 = ana.load('/work/results/e1_width'); d1 = d1[(d1.seed < 4) & d1.width.isin([16, 32, 64, 128])].copy(); d1['op'] = 'add'
df = pd.concat([d1, df], ignore_index=True)
th = lambda x: f'{int(x):,}'.replace(',', r'\,')
rows, L = [], []
for (op, w), g in df.groupby(['op', 'width']):
    tg = np.median(np.where(g.gen, g.t_gen, np.inf)); tf = np.median(np.where(g.fit, g.t_fit, np.inf))
    rows.append(dict(op=op, width=w, n=len(g), fit=int(g.fit.sum()), gen=int(g.gen.sum()), t_fit=tf, t_gen=tg, va_fit=g.va_fit.median(), fin_va=g.fin_va.median(), mem_first=int(g.mem_first.sum())))
T = pd.DataFrame(rows); T.to_csv('/work/tables/e6_table.csv', index=False); print(T.to_string())
name = {'add': '$a+b$', 'sub': '$a-b$', 'x2y2': '$a^2+b^2$'}
for _, r in T.sort_values(['op', 'width'], key=lambda c: c.map({'add': 0, 'sub': 1, 'x2y2': 2}) if c.name == 'op' else c).iterrows():
    L.append(f"{name[r.op]} & {int(r.width)} & {int(r.fit)}/{int(r.gen)} & {int(r.mem_first)} & {th(r.t_fit) if np.isfinite(r.t_fit) else '$>$30k'} & {th(r.t_gen) if np.isfinite(r.t_gen) else '$>$30k'} & {r.va_fit:.2f} & {r.fin_va:.2f} \\\\")
open('/work/tables/e6_tab.tex', 'w').write('\\begin{tabular}{llcccccc}\n\\toprule\nop & $d$ & fit/gen & mem. & $t_{\\mathrm{fit}}$ & $t_{\\mathrm{gen}}$ & $a^{\\mathrm{val}}_{\\mathrm{fit}}$ & final val\\\\\n\\midrule\n' + '\n'.join(L) + '\n\\bottomrule\n\\end{tabular}\n')
