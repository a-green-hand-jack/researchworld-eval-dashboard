import numpy as np, sys
import data_mats as dm
S, cfgs, info = dm.api_matrix("claude-opus-4-5")
ok = ~np.isnan(S).any(0)
S = S[:, ok]; U = info["unparsed"][:, ok]
print("complete questions", S.shape)
m = S.mean(1)
print("config acc: min %.3f med %.3f max %.3f sd %.4f; cfg0 %.3f" % (m.min(), np.median(m), m.max(), m.std(), m[0]))
print("unparsed rate per cfg: max %.3f mean %.4f" % (U.mean(1).max(), U.mean()))
C = np.corrcoef(S); K = len(m)
print("mean pairwise corr", (C.sum() - K) / (K * (K - 1)))
order = np.argsort(-m)
for k in list(order[:5]) + list(order[-3:]):
    print(round(m[k], 3), round(U[k].mean(), 3), cfgs[k])
