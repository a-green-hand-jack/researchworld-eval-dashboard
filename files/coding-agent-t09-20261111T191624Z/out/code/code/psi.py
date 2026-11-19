"""Exact population (Bernoulli) bias of 1-hop regression under multi-hop linear-in-means interference:
B = -beta * sum_{k>=2} lam^k (1 - psi_k),  psi_k = r_k + u_k/q,
r_k = mean_i (W^k)_ii ,  u_k = mean_i sum_j (W^k)_ij W_ij ,  q = u_1 = mean_i sum_j W_ij^2.
Prints psi_k for the graphs; used in the paper (Table / text)."""
import sys, json
import numpy as np
from sim import build_graph, World

def psi(A, K=14):
    W = (A.multiply(1.0 / np.asarray(A.sum(1)))).tocsr()  # row-normalised
    n = A.shape[0]
    Wd = W.toarray()
    Wk = Wd.copy()
    q = float(np.mean(np.asarray(W.multiply(W).sum(1)).ravel()))
    out = {}
    for k in range(2, K + 1):
        Wk = (W.T @ Wk.T).T          # Wk @ W  -> (W^{k-1}) W = W^k  (dense x sparse)
        r = float(np.mean(np.diag(Wk)))
        u = float(np.mean(np.asarray(W.multiply(Wk).sum(1)).ravel()))
        out[k] = (r, u / q)
    return q, out

if __name__ == "__main__":
    res = {}
    for name in ["er", "egofb", "stanford3"]:
        spec = dict(name="er", n=4000, d=30) if name == "er" else dict(name=name)
        A = build_graph(spec, 100 if name == "er" else 0)
        q, out = psi(A)
        res[name] = dict(q=q, psi={k: v[0] + v[1] for k, v in out.items()}, r={k: v[0] for k, v in out.items()}, u={k: v[1] for k, v in out.items()})
        print(name, "q=%.4f" % q, {k: round(v[0] + v[1], 3) for k, v in list(out.items())[:5]}, flush=True)
        for lam in [0.2, 0.4, 0.6, 0.8]:
            B = -sum(lam ** k * (1 - (v[0] + v[1])) for k, v in out.items())
            Btree = -lam ** 2 / (1 - lam)
            print("   lam", lam, "exact(trunc K=14) B=%.3f  tree-like %.3f" % (B, Btree))
    json.dump(res, open("/work/results/psi.json", "w"))
