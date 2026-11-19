"""Assemble paper tables from results/summary_main.pkl (written by analyze_main.py)."""
import sys, os, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from analyze_main import NAME, ALL

S = pickle.load(open('/work/results/summary_main.pkl', 'rb'))
REGS_P = [r for r in ['iid', 'up50', 'up75', 'fam'] if (r, 50) in S]
ROWS = ['rand/mean', 'strat/mean', 'anchor/mean', 'anchor_irt/mean', 'dopt/mean', 'maxvar/mean', 'rand/ridge', 'rand/knn',
        'rand/pirt', 'rand/gpirt', 'anchor_irt/gpirt', 'rand/pirt_cal', 'rand/cf', 'strat/cf', 'rand/eb0', 'strat/eb0', 'rand/eb1']
GROUPS = {'rand/mean': 'Plain mean of the subset', 'rand/ridge': 'Model-based estimators', 'rand/cf': 'Unbiased / adaptive (ours)'}


def cell_rel(r, ref):
    if ref: return '1'
    return f"{r['rel']:.2f}\\,{{\\scriptsize[{r['lo']:.2f},{r['hi']:.2f}]}}"


def combined(k, fn, rows=ROWS):
    with open(fn, 'w') as fh:
        for c in rows:
            cells = []
            for reg in REGS_P:
                r = S[(reg, k)][c]
                cells += [cell_rel(r, c == 'rand/mean'), f"{r['sp']:.3f}"]
            fh.write(f"{NAME[c]} & " + ' & '.join(cells) + ' \\\\\n')
            if c in ('strat/mean', 'rand/knn', 'anchor_irt/gpirt'):
                pass


def full_table(k, reg, fn):
    with open(fn, 'w') as fh:
        for c in ALL:
            r = S[(reg, k)][c]
            rel = '1 (ref.)' if c == 'rand/mean' else f"{r['rel']:.2f} [{r['lo']:.2f}, {r['hi']:.2f}]"
            fh.write(f"{NAME[c]} & {rel} & {r['mae']:.2f} & {r['sp']:.3f} & {r['kt']:.3f} & {r['bias']:+.2f} \\\\\n")


os.makedirs('/work/results/tables', exist_ok=True)
for k in [10, 25, 50, 100, 200]:
    combined(k, f'/work/results/tables/combined_k{k}.tex')
    for reg in REGS_P:
        full_table(k, reg, f'/work/results/tables/full_{reg}_k{k}.tex')
print('ok')


def rel_by_k(reg, fn):
    with open(fn, 'w') as fh:
        for c in ALL:
            cells = []
            for k in [10, 25, 50, 100, 200]:
                r = S[(reg, k)][c]
                cells.append('1' if c == 'rand/mean' else f"{r['rel']:.2f}")
            fh.write(f"{NAME[c]} & " + ' & '.join(cells) + ' \\\\\n')


def sp_by_k(reg, fn):
    with open(fn, 'w') as fh:
        for c in ALL:
            fh.write(f"{NAME[c]} & " + ' & '.join(f"{S[(reg, k)][c]['sp']:.3f}" for k in [10, 25, 50, 100, 200]) + ' \\\\\n')


for reg in REGS_P:
    rel_by_k(reg, f'/work/results/tables/relk_{reg}.tex')
    sp_by_k(reg, f'/work/results/tables/spk_{reg}.tex')


# \input files must not end with a row terminator: the paper adds "\\" itself after \input (a trailing "\\" before the
# end of an input file followed by \bottomrule/\midrule breaks booktabs).
import glob
for f in glob.glob('/work/results/tables/*.tex'):
    if os.path.basename(f).startswith(('combined_', 'full_', 'relk_', 'spk_', 'cover', 'datasets')):
        t = open(f).read().rstrip()
        if t.endswith('\\\\'):
            open(f, 'w').write(t[:-2].rstrip() + '\n')
