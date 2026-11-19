"""Dataset summary table (after removing duplicate model names)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from bplib import load_bench, BENCHES
from analyze_lib import BENCH_LABEL
rows = []
with open('/work/results/tables/datasets.tex', 'w') as fh:
    for b in ['arc_challenge', 'bbh', 'gpqa', 'ifeval', 'mmlu_pro', 'musr', 'openllm_math', 'commonsense', 'gsm', 'legalbench', 'math', 'med_qa', 'mmlu']:
        z = np.load(f'/work/data/{b}.npz'); raw = z['X'].shape[0]
        X, models = load_bench(b); s = X.mean(1)
        const = int(((X.mean(0) == 0) | (X.mean(0) == 1)).sum())
        fh.write(f'{BENCH_LABEL[b]} & {raw} & {X.shape[0]} & {X.shape[1]} & {100*s.mean():.1f} & {100*s.min():.1f}--{100*s.max():.1f} & {100*const/X.shape[1]:.1f}\\% \\\\\n')
        print(b, raw, X.shape, s.mean().round(3), s.min().round(3), s.max().round(3), const)
