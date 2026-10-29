"""Shared helpers for the figure generators: paths, sample loading, plotting style.

Layout assumed: <root>/code/figures/ (this file), <root>/outputs/ (analysis results),
<root>/report/images/ (figures written here). Run any generator from any directory.
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUTPUTS = os.path.join(ROOT, 'outputs')
IMAGES = os.path.join(ROOT, 'report', 'images')
DATA = os.path.join(ROOT, 'data') if os.path.isdir(os.path.join(ROOT, 'data')) else '/initial-state/inputs/2'
os.makedirs(IMAGES, exist_ok=True)

SOURCES = {
    'M33_X-7': dict(label='M33 X-7', file='M33_X-7_samples.dat', color='#0072B2'),
    'IRAS_09149-6206': dict(label='IRAS 09149-6206', file='IRAS_09149-6206_samples.dat', color='#D55E00'),
}
COMB = '#333333'
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})


def load(key, data_dir=DATA):
    return np.loadtxt(f"{data_dir}/{SOURCES[key]['file']}")  # columns: M [Msun], a*


def summary(rate='leaver'):
    name = 'summary_leaver.json' if rate == 'leaver' else 'summary.json'
    return json.load(open(os.path.join(OUTPUTS, name)))


def save(fig, name):
    path = os.path.join(IMAGES, name)
    fig.savefig(path, dpi=170)
    print('wrote', path)


def sci(x):
    e = int(np.floor(np.log10(x)))
    return rf'${x / 10**e:.2f}\times10^{{{e}}}$'
