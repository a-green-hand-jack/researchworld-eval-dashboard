"""Data audit of the per-item 0/1 score matrices (context position).

Usage: python3 audit/data_audit.py <path to benchmark-prediction checkout at commit 55faff4...> > audit/data_audit.md
Reads data/scores/<name>.jbl (+ <name>_models.jbl for Open LLM files); no randomness.
"""
import collections, os, sys
import joblib
import numpy as np

root = sys.argv[1]
names = ["mmlu_pro", "bbh", "gpqa", "ifeval", "musr", "openllm_math", "arc_challenge",
         "commonsense", "gsm", "legalbench", "math", "med_qa", "mmlu"]
print("| benchmark | models | items | rows unique by name | identical-row surplus | models acc==0 | items acc==0 | items acc==1 | acc SD | mean pairwise item corr (500 items) |")
print("|---|---|---|---|---|---|---|---|---|---|")
rng = np.random.RandomState(0)
for n in names:
    d = np.asarray(joblib.load(f"{root}/data/scores/{n}.jbl")).astype(float)
    mp = f"{root}/data/scores/{n}_models.jbl"
    uniq = len(set(joblib.load(mp))) if os.path.exists(mp) else "n/a"
    keys = collections.Counter(r.tobytes() for r in d)
    surplus = sum(v - 1 for v in keys.values())
    a, it = d.mean(1), d.mean(0)
    idx = rng.choice(d.shape[1], min(500, d.shape[1]), replace=False)
    with np.errstate(all="ignore"):
        c = np.corrcoef(d[:, idx], rowvar=False)
    m = np.nanmean(c[np.triu_indices_from(c, 1)])
    print(f"| {n} | {d.shape[0]} | {d.shape[1]} | {uniq} | {surplus} | {(a==0).sum()} | {(it==0).sum()} | {(it==1).sum()} | {a.std():.3f} | {m:.3f} |")
