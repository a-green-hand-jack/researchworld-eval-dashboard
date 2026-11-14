"""Check that re-running the main experiment with the extended code (tag main2) reproduces the first-version results
(tag main, kept in results/old_main/raw_main_v1) exactly for all estimators that existed in both versions."""
import pickle, glob, os
mx = 0.0; n = 0
for f in sorted(glob.glob('/work/results/raw_main2/*.pkl')):
    g = '/work/results/old_main/raw_main_v1/' + os.path.basename(f)
    if not os.path.exists(g): continue
    a = {(r['k'], r['sel'], r['est']): r for r in pickle.load(open(f, 'rb'))['rows']}
    for r in pickle.load(open(g, 'rb'))['rows']:
        q = a[(r['k'], r['sel'], r['est'])]
        for m in ['mae', 'rmse', 'bias', 'spearman', 'kendall']:
            mx = max(mx, abs(q[m] - r[m]))
    n += 1
print(n, 'tasks compared; max abs difference', mx)
