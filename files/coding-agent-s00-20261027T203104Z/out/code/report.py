"""Generate paper numbers from the experiment's machine-readable output."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent
s = json.loads((root/'results/summary.json').read_text())
lines = []
for label, key in [('Universal bound', 'bound'), ('$n$ only', 'n_only'), ('Four statistics', 'four_stats')]:
    cells = [label]
    for p in ['interpolation','leave_family_out']:
        d=s[p][key]; a,b=d['mc95']
        cells.append(f"{d['macro_mape']:.1f} [{a:.1f}, {b:.1f}]")
    lines.append(' & '.join(cells)+r' \\')
(root/'results/table.tex').write_text(
    '\\begin{tabular}{lrr}\n\\toprule\nMethod & Size interpolation & Leave one family out\\\\\n\\midrule\n'
    + '\n'.join(lines)+'\n\\bottomrule\n\\end{tabular}\n')

