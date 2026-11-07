"""Validation of the greedy edit search against exhaustive search on tiny boards,
sensitivity of the greedy to its step fraction, and IJ-vs-bootstrap standard errors."""
import itertools, json, sys
import numpy as np
from bt import *
import datasets as ds

rng = np.random.default_rng(12345)
MOVES = {}
def moves(kind):
    mv = []
    if kind == "drop":
        mv = [(c, l, -1) for c in range(3) for l in range(3)]
    elif kind == "relabel":
        mv = [(c, l, l2) for c in range(3) for l in range(3) for l2 in range(3) if l != l2]
    else:
        mv = [(c, -1, l2) for c in range(3) for l2 in (0, 2)]
    return mv

def exhaustive_less_than(b, c, th0, kind, K):
    """Is there an edit set of size < K that flips? Return min size found (or None)."""
    mv = moves(kind)
    for k in range(1, K):
        for comb in itertools.combinations_with_replacement(range(len(mv)), k):
            N = b.N.copy(); ok = True
            for idx in comb:
                cc, s, d = mv[idx]
                if s >= 0:
                    N[cc, s] -= 1
                    if N[cc, s] < 0: ok = False; break
                if d >= 0: N[cc, d] += 1
            if not ok: continue
            if c @ b.fit(N, th0) <= 0:
                return k
    return None

out = {}
for kind in ["drop", "relabel", "insert"]:
    res = []
    tries = 0
    while len(res) < 40 and tries < 400:
        tries += 1
        s = rng.normal(0, 0.5, 3)
        pairs = np.array([[0, 1], [0, 2], [1, 2]])
        N = np.zeros((3, 3), int)
        for c, (a, bb) in enumerate(pairs):
            pw = 1 / (1 + np.exp(-(s[a] - s[bb])))
            for _ in range(8):
                u = rng.random()
                N[c, 2 if u < pw * 0.75 else (1 if u < pw * 0.75 + 0.2 else 0)] += 1
        b = Board(["a", "b", "c"], pairs, N)
        th = b.fit(); o = np.argsort(-th[:3])
        i, j = o[0], o[1]
        g = min_edits(b, i, j, kind, max_k=24, th0=th)
        if not np.isfinite(g["k"]) or g["k"] > 6 or g["k"] < 2: continue
        c = b.contrast(i, j)
        better = exhaustive_less_than(b, c, th, kind, int(g["k"]))
        res.append((int(g["k"]), better))
    n_sub = sum(1 for _, bt in res if bt is not None)
    out[kind] = dict(n=len(res), greedy_suboptimal=n_sub,
                     mean_greedy=float(np.mean([r[0] for r in res])),
                     mean_gap=float(np.mean([r[0] - (r[1] if r[1] is not None else r[0]) for r in res])),
                     detail=res)
    print(kind, {k: v for k, v in out[kind].items() if k != "detail"}, flush=True)

# step-fraction sensitivity on real boards
sens = []
boards = [ds.mtbench_human(), ds.mtbench_gpt4(), ds.arena55k()]
for b in boards:
    th = b.fit(); o = np.argsort(-th[:b.m])
    pairs = [(o[r], o[r + 1]) for r in range(0, min(b.m - 1, 20))]
    for kind in ["drop", "relabel", "insert"]:
        for (i, j) in pairs:
            ks = [min_edits(b, i, j, kind, int(0.3 * b.n), th0=th, frac=f)["k"] for f in (0.1, 0.25, 0.5, 1.0)]
            sens.append(dict(board=b.name, kind=kind, i=int(i), j=int(j), ks=ks))
out["frac_sensitivity"] = sens
a = np.array([s["ks"] for s in sens], float)
ok = np.isfinite(a).all(1)
rel = a[ok] / a[ok][:, [0]]
print("frac sensitivity: median ratio k(f)/k(0.1) for f=0.1,.25,.5,1:", np.median(rel, 0), "max", rel.max(0))

# IJ vs bootstrap SE
se = []
for b in boards:
    th = b.fit(); o = np.argsort(-th[:b.m])
    bs = b.bootstrap(300, rng, th)
    for r in range(min(b.m - 1, 10)):
        i, j = o[r], o[r + 1]
        se.append(dict(board=b.name, ij=b.ij_se(th, i, j), boot=float(np.std(bs[:, i] - bs[:, j], ddof=1))))
out["se"] = se
d = np.array([[s["ij"], s["boot"]] for s in se])
print("IJ/boot se ratio: median %.3f min %.3f max %.3f" % (np.median(d[:, 0] / d[:, 1]), (d[:, 0] / d[:, 1]).min(), (d[:, 0] / d[:, 1]).max()))
json.dump(out, open("/work/results/validate.json", "w"), default=lambda x: float(x) if np.isfinite(x) else "inf")
