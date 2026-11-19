"""Render manuscript-only tables from measured CSVs; no experiments or new inference."""
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'paper_tables'
OUT.mkdir(exist_ok=True)

def table(path, header, rows):
    lines = [r'\begingroup\footnotesize', r'\begin{tabular}{' + 'l'*len(header) + '}',
             r'\toprule', ' & '.join(header) + r' \\', r'\midrule']
    lines += [' & '.join(map(str,row)) + r' \\' for row in rows]
    lines += [r'\bottomrule', r'\end{tabular}', r'\endgroup']
    path.write_text('\n'.join(lines)+'\n')

a = pd.read_csv(ROOT/'analysis120/exact_macro.csv')
a = a[a.method.eq('antithetic')]
metrics = ['absolute_l1','normalized_l1','material_sign_agreement','pairwise_top3_match','nogueira_stability']
def ci(row,k):
    return f'{row[k]:.4f} [{row[k+"_lo"]:.4f}, {row[k+"_hi"]:.4f}]'
macro_rows = []
for key,label in zip(metrics, ['L1 $\\downarrow$','Normalized L1 $\\downarrow$','Material sign $\\uparrow$','Pair match $\\uparrow$','Stability $\\uparrow$']):
    macro_rows.append([label] + [r'\shortstack{' + f'{r[key]:.4f}' + r'\\{' + f'[{r[key+"_lo"]:.4f}, {r[key+"_hi"]:.4f}]' + '}}' for _,r in a.iterrows()])
table(OUT/'macro_metrics.tex', ['Metric'] + [f'$P={int(p)}$' for p in a.budget], macro_rows)
c = pd.read_csv(ROOT/'analysis120/expansion_cohort_headlines.csv')
c = c[c.dataset.eq('exact_macro')]
labels = {'exploratory_first30':'Exploratory first 30','heldout_next90':'Held-out next 90','combined120_main':'Combined 120'}
table(OUT/'cohorts.tex', ['Cohort','$n$','$P$','Exact-game macro match [95\\% CI]'],
      [[labels[r.stage],int(r.n),int(r.budget),ci(r,'top3_match')] for _,r in c.iterrows()])
print('Rendered',OUT)
