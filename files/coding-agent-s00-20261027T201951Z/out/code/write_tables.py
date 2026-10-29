"""Regenerate numerical LaTeX tables from the recorded results."""
from pathlib import Path
import json
p=Path(__file__).resolve().parent
s=json.loads((p/'results/summary.json').read_text())
with open(p/'results/metrics.tex','w') as f:
 f.write(r'\begin{tabular}{lrr}\toprule'+'\n'+r'Predictor & Familiar families (22) & New families (12) \\ \midrule'+'\n')
 for key,label in [('statistics','Four statistics'),('size_only',r'Fitted $a n\log n$'),('bound',r'Upper bound $2m(n-1)$')]:
  cells=[]
  for split in ['test','ood']:
   r=s['metrics'][split][key];lo,hi=r['graph_boot_ci']
   cells.append(f"{r['mape']:.1f} [{lo:.1f}, {hi:.1f}]")
  f.write(label+' & '+' & '.join(cells)+r' \\'+'\n')
 f.write(r'\bottomrule\end{tabular}'+'\n')
with open(p/'results/families.tex','w') as f:
 f.write(r'\begin{tabular}{lrrrrrrrrr}\toprule'+'\n')
 f.write('Family & Path & Cycle & Star & Clique & Grid & ER & Tree & Barbell & Lollipop'+r' \\ \midrule'+'\n')
 f.write('Count & '+' & '.join(str(r['count']) for r in s['family'])+r' \\'+'\n')
 f.write(r'Error (\%) & '+' & '.join(f"{r['mape']:.1f}" for r in s['family'])+r' \\'+'\n')
 f.write(r'Bias (\%) & '+' & '.join(f"{r['bias_pct']:+.1f}" for r in s['family'])+r' \\ \bottomrule\end{tabular}'+'\n')
