"""Recompute the derived marks of the result tables from their own entries.

For each main-results table: per column, the best and second-best value over
the comparison rows (other open models) and our model, and the Delta row
(ours minus best other open model). For the ablation table: drops relative to
the full model. Usage: python3 scripts/check_tables.py <tables-dir>
"""
import re
import sys
from pathlib import Path

def rows(tex):
    out = []
    for line in tex.splitlines():
        line = line.strip().rstrip('\\').strip()
        if '&' not in line or line.startswith('&') or 'multicolumn' in line:
            continue
        cells = [c.strip() for c in line.replace(r'\&', ' and ').split('&')]
        name = re.sub(r'\\[a-z]+\{?|[{}]', '', cells[0]).strip()
        vals = []
        for c in cells[1:]:
            m = re.search(r'[-+]?\d+\.\d+', c)
            vals.append(float(m.group()) if m else None)
        out.append((name, vals))
    return out

def main_table(path, ours, others_from, cols):
    print(f'== {path.name}')
    rs = rows(path.read_text())
    names = [n for n, _ in rs]
    start = names.index(others_from)
    others = [r for r in rs[start:] if 'VL-Rethinker' not in r[0] and 'Delta' not in r[0]
              and 'model' not in r[0]]
    me = next(v for n, v in rs if n.startswith(ours))
    stated = next(v for n, v in rs if 'Delta' in n)
    for j, col in enumerate(cols):
        cand = sorted(((v[j], n) for n, v in others if v[j] is not None), reverse=True)
        allc = sorted(cand + [(me[j], ours)], reverse=True)
        delta = round(me[j] - cand[0][0], 1)
        flag = '' if abs(delta - stated[j]) < 1e-6 else '  <-- stated %+.1f' % stated[j]
        print(f'{col:11s} best={allc[0]} 2nd={allc[1]} best-other={cand[0]} delta={delta:+.1f}{flag}')

def ablation(path):
    print(f'== {path.name}')
    rs = [r for r in rows(path.read_text()) if r[0] != 'Model']
    full = rs[0][1]
    for n, v in rs[1:]:
        print(f'{n:28s}', ' '.join('%+.1f' % (a - b) if a is not None else '  -  '
                                   for a, b in zip(v[2:], full[2:])))

if __name__ == '__main__':
    d = Path(sys.argv[1])
    cols = ['MathVista', 'MathVerse', 'MathVision', 'MMMU-Pro', 'MMMU', 'EMMA', 'MEGA']
    main_table(d / 'table_rr.tex', 'VL-Rethinker-72B', 'Llama4-Scout-109B', cols)
    main_table(d / 'table_le.tex', 'VL-Rethinker-7B', 'InternVL2-8B', cols)
    ablation(d / 'table_im.tex')
