"""Measurement-noise reference from `scores_per_experiment` of the MTEB result files (repeat runs inside one result file).

For a cell (model, task): the score is the mean over hf_subsets of main_score; main_score of a subset is the mean over its
experiments (repeated runs on different train subsets / seeds).  We estimate the variance of the *cell value* due to the
experiment draw as  (1/S^2) * sum_subsets var_exp / n_exp  and, as the variance of ONE repeat of the cell,
 (1/S^2) * sum_subsets var_exp (what a single re-run of the benchmark would differ by).
Only tasks with >= 2 experiments have an estimate (typically classification-type tasks); others are NaN.

usage: python noise_floor.py <mteb results dir> <matrix name> <out csv>
"""
import json, os, sys, glob
import numpy as np, pandas as pd

SPLIT_PREF = ["test", "validation", "dev", "train"]

def cell_noise(f):
    d = json.load(open(f))
    sc = d.get("scores", {})
    split = next((s for s in SPLIT_PREF if s in sc), next(iter(sc), None))
    if split is None or not sc[split]:
        return None
    v_mean, v_one, S, nexp = 0.0, 0.0, 0, 0
    for e in sc[split]:
        S += 1
        spe = e.get("scores_per_experiment")
        if not spe or len(spe) < 2 or not isinstance(e.get("main_score"), (int, float)):
            continue
        # metric used as main_score = the key whose mean over experiments equals the subset main_score
        best = None
        for k in spe[0]:
            xs = [x.get(k) for x in spe]
            if all(isinstance(x, (int, float)) for x in xs) and abs(np.mean(xs) - e["main_score"]) < 1e-5:
                best = xs; break
        if best is None:
            continue
        v = np.var(best, ddof=1)
        v_one += v; v_mean += v / len(best); nexp = max(nexp, len(best))
    if nexp == 0 or S == 0:
        return None
    return v_mean / S ** 2, v_one / S ** 2, nexp, S

def main(res, name, out):
    z = np.load(os.path.join(os.path.dirname(__file__), '..', 'data', 'matrices', name + '.npz'), allow_pickle=True)
    Y = z['Y']; models, tasks = z['models'].astype(str), z['benches'].astype(str)
    rows = []
    for i, m in enumerate(models):
        for rev in sorted(glob.glob(os.path.join(res, m, '*'))):
            for j, t in enumerate(tasks):
                f = os.path.join(rev, t + '.json')
                if np.isnan(Y[i, j]) or not os.path.exists(f):
                    continue
                r = cell_noise(f)
                if r:
                    rows.append((m, t, *r))
    df = pd.DataFrame(rows, columns=['model', 'task', 'var_cell', 'var_single', 'n_exp', 'n_subsets'])
    df = df.groupby(['model', 'task']).first().reset_index()
    df.to_csv(out, index=False)
    print(name, len(df), 'cells with noise estimate of', int(np.isfinite(Y).sum()), flush=True)

if __name__ == '__main__':
    main(*sys.argv[1:4])
