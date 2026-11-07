"""Shared style, colours and readers for the figure/table scripts.

Experiment results are read from <repo root>/results (paper-repo layout), else from a checkout of experiment-repo given by $FIGTAB_EXP.
Every plotted number comes from a CSV under <exp>/results; nothing is typed here.
"""
import os, subprocess
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_default = ROOT if os.path.isdir(os.path.join(ROOT, 'results', 'summary')) else '/hutian/exp'
EXP = os.environ.get('FIGTAB_EXP', _default)
SUM = os.path.join(EXP, 'results', 'summary')
THEORY = os.path.join(EXP, 'results', 'theory')
FIGDIR = os.path.join(ROOT, 'figures')
TABDIR = os.path.join(ROOT, 'tables')
W = 5.5  # ICLR 2027 text width, inches

plt.rcParams.update({
    'font.size': 7, 'axes.titlesize': 7.5, 'axes.labelsize': 7, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5,
    'legend.fontsize': 6.5, 'axes.linewidth': .6, 'lines.linewidth': 1.2, 'lines.markersize': 2.8,
    'axes.spines.top': False, 'axes.spines.right': False, 'pdf.fonttype': 42, 'ps.fonttype': 42,
    'figure.dpi': 150, 'savefig.bbox': 'tight', 'savefig.pad_inches': .02,
})

# selector colours (Okabe-Ito, colour-blind safe); same selector = same colour in every figure
SEL_COLOR = {'random': '#7f7f7f', 'gv_fa': '#0072B2', 'dopt': '#D55E00', 'gv_emp': '#009E73', 'kcenter': '#CC79A7',
             'lev': '#E69F00', 'qr': '#56B4E9', 'central': '#8c564b', 'rawvar': '#000000', 'popular': '#bcbd22',
             'oracle': '#000000'}
SEL_LABEL = {'random': 'random', 'gv_fa': 'greedy cond. variance (FA)', 'dopt': 'greedy log-det (D-opt.)',
             'gv_emp': 'greedy cond. variance (empirical)', 'kcenter': 'k-center', 'lev': 'leverage score',
             'qr': 'pivoted QR', 'central': 'most central', 'rawvar': 'highest variance', 'popular': 'most covered',
             'oracle': 'oracle (uses target row)'}
METHOD_LABEL = {'mean': 'column mean', 'avgreg': 'average-score regression', 'fa': 'factor-analysis posterior',
                'ridge': 'ridge', 'knn': 'kNN over models', 'krr': 'kernel ridge', 'pcals': 'PCA-LS'}
DATASET_LABEL = {'mteb_dense56': 'MTEB-56 (152 models x 56 tasks)', 'mteb_dense': 'MTEB-275', 'mteb_mid': 'MTEB-357',
                 'mteb_sparse': 'MTEB-472 (sparse)', 'olb': 'Open LLM Leaderboard', 'helm': 'HELM Lite-10', 'helm_lite_ext': 'HELM Lite-28',
                 'helm_mmlu': 'HELM-MMLU (57 subjects)', 'livebench': 'LiveBench'}

def curves(run):
    return pd.read_csv(os.path.join(SUM, f'curves_{run}.csv'))

def read(name, sub=SUM):
    return pd.read_csv(os.path.join(sub, name))

def exists(name, sub=SUM):
    return os.path.exists(os.path.join(sub, name))

def kticks(ax, ks=(1, 2, 4, 8, 16, 32, 64), kmax=None):
    if kmax: ks = [k for k in ks if k <= kmax * 1.05]
    ax.set_xscale('log'); ax.set_xticks(ks); ax.set_xticklabels([str(k) for k in ks]); ax.minorticks_off()

def band(ax, d, col='nmse', color='k', label=None, ls='-', marker='o', alpha=.15, lo=None, hi=None):
    d = d.sort_values('k')
    ax.plot(d.k, d[col], ls, marker=marker, color=color, label=label)
    ax.fill_between(d.k, d[lo or col + '_lo'], d[hi or col + '_hi'], color=color, alpha=alpha, lw=0)

def save(fig, name):
    os.makedirs(FIGDIR, exist_ok=True)
    p = os.path.join(FIGDIR, name)
    fig.savefig(p); plt.close(fig)
    print('wrote', p)

def exp_rev():
    try:
        return subprocess.check_output(['git', '-C', EXP, 'rev-parse', 'HEAD']).decode().strip()
    except Exception:
        return 'unknown'
