"""Re-check ILP solutions on real boards: apply the returned task set to the
score matrix and verify with the independent reference rule that t is first,
and that the k-1 relaxation (dropping any task) is not (local minimality)."""
import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis"))
from common import *
rng = np.random.default_rng(0)
bad = 0; cnt = 0
for board in ["helm", "olb"]:
    if board == "helm": S = load_helm().values
    else:
        o, S = load_olb("main"); S = S[np.argsort(-S.mean(1))[:600]]
    for t in rng.choice(len(S), 8, replace=False):
        for rule in R.ORDINAL:
            for d in [10., 100.]:
                r = V.min_k_ordinal(S, int(t), rule, d, 100., return_set=True)
                if r == V.INF or r == 0: continue
                k, T = r; cnt += 1
                v = np.minimum(S[t] + d, 100.); S2 = S.copy(); S2[t, T] = v[T]
                if not R.is_first(S2, int(t), rule): bad += 1; print("NOT FIRST", board, rule, t, d)
                for j in T:
                    S3 = S.copy(); T2 = [x for x in T if x != j]; S3[t, T2] = v[T2]
                    if R.is_first(S3, int(t), rule): bad += 1; print("NOT MINIMAL(local)", board, rule, t, d)
print("checked", cnt, "bad", bad); sys.exit(bad > 0)
