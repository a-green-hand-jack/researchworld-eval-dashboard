"""Wraps the row files written by tab_*.py / fig_*.py into complete tabular environments (\\input of bare rows inside
tabular breaks booktabs rules). Run after all tab_*.py scripts."""
from analysis_common import *
SPEC = {
    'tab_e2': ('llllllll', r'Graph & Design & DM & OLS-x & OLS-quad & Oracle & GBDT & H\'ajek \\'),
    'tab_e3': ('llrrrrrr', r'Mech. & Design & bias & SD$_S$ & SD$_N$ & RMSE & $\|w\|_1$ & $\|w\|_2$ \\'),
    'tab_e7': ('lllrrrrrrr', r'Graph & Mech. & Des. & bias & RMSE & iid & HC3 & CR & $\overline{\rm SE}_{iid}$/SD & $\overline{\rm SE}_{CR}$/SD \\'),
    'tab_e7_full': ('lllrrrrrrr', r'Graph & Mech. & Des. & bias & RMSE & iid & HC3 & CR & $\overline{\rm SE}_{iid}$/SD & $\overline{\rm SE}_{CR}$/SD \\'),
    'tab_theory': ('lrrrrr', r'Mech. & $p$ & empirical & s.e. & predicted & diff \\'),
    'tab_e10': ('llrr|rrrr|rrrr', r'Graph & Res. & $K$ & cut & DM & OLS-x & Orac. & GBDT & DM & OLS-x & Orac. & GBDT \\'),
    'tab_e11': ('lllrrrr', r'Graph & Des. & Est. & 0 & 0.5 & 1 & 2 \\'),
}
for k, (cs, hdr) in SPEC.items():
    rows = open(f'{TAB}/{k}.tex').read().strip()
    open(f'{TAB}/{k}_tab.tex', 'w').write('\\begin{tabular}{%s}\n\\toprule\n%s\n\\midrule\n%s\n\\bottomrule\n\\end{tabular}\n' % (cs, hdr, rows))
