"""Fit and evaluate predictors of log cover time; leave-one-family-out CV.
Usage: python3 analyze.py results.json
"""
import json, math, sys, statistics as st
from collections import defaultdict

def solve(M, b):
    n = len(b); M = [r[:] + [b[i]] for i, r in enumerate(M)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c])); M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                for k in range(c, n + 1): M[r][k] -= f * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]

def ols(X, y, lam=1e-9):
    k = len(X[0])
    XtX = [[sum(x[i] * x[j] for x in X) + (lam if i == j else 0) for j in range(k)] for i in range(k)]
    Xty = [sum(x[i] * t for x, t in zip(X, y)) for i in range(k)]
    return solve(XtX, Xty)

def feats(r, kind):
    L = math.log
    if kind == "bound":   return [1.0]  # calibration constant only, on log(2m(n-1))
    if kind == "nm":      return [1.0, L(r["n"]), L(r["m"])]
    if kind == "nmD":     return [1.0, L(r["n"]), L(r["m"]), L(r["D"])]
    if kind == "nmDd":    return [1.0, L(r["n"]), L(r["m"]), L(r["D"]), L(r["dmax"])]
    raise ValueError(kind)

def target_offset(r, kind):
    return L_bound(r) if kind == "bound" else 0.0

def L_bound(r): return math.log(r["bound"])

def fit_predict(train, test, kind):
    y = [math.log(r["cover"]) - target_offset(r, kind) for r in train]
    X = [feats(r, kind) for r in train]
    w = ols(X, y)
    return [math.exp(sum(a * b for a, b in zip(w, feats(r, kind))) + target_offset(r, kind)) for r in test]

def mdape(pred, rows):
    return st.median(abs(p - r["cover"]) / r["cover"] for p, r in zip(pred, rows))

def main(path):
    rows = json.load(open(path))["rows"]
    kinds = ["bound", "nm", "nmD", "nmDd"]
    out = {}
    # ratio of simulated cover time to 2m(n-1) bound
    rat = [r["cover"] / r["bound"] for r in rows]
    print(f"graphs={len(rows)}  C/bound: median={st.median(rat):.3f} min={min(rat):.3f} max={max(rat):.3f}")
    print(f"max MC rel. CI half-width = {max(r['ci']/r['cover'] for r in rows):.4f}")
    # Leave-one-family-out CV
    fams = sorted(set(r["family"] for r in rows))
    for kind in kinds:
        errs = defaultdict(list); allp = []; allr = []
        for f in fams:
            tr = [r for r in rows if r["family"] != f]; te = [r for r in rows if r["family"] == f]
            p = fit_predict(tr, te, kind)
            for pi, r in zip(p, te):
                e = abs(pi - r["cover"]) / r["cover"]; errs[f].append(e)
                allp.append(pi); allr.append(r)
        all_e = [e for f in fams for e in errs[f]]
        out[kind] = dict(mdape=st.median(all_e), mape=st.mean(all_e),
                         per_family={f: st.median(errs[f]) for f in fams})
        print(f"{kind:6s} LOFO median APE={st.median(all_e):.3f} mean APE={st.mean(all_e):.3f}")
    print("\nper-family LOFO median APE:")
    print(f"{'family':12s}" + "".join(f"{k:>9s}" for k in kinds))
    for f in fams:
        print(f"{f:12s}" + "".join(f"{out[k]['per_family'][f]:9.3f}" for k in kinds))
    full = {k: ols([feats(r, k) for r in rows], [math.log(r["cover"]) - target_offset(r, k) for r in rows]) for k in kinds}
    print("\nfull-data coefficients (log scale):")
    for k in kinds: print(k, [round(c, 3) for c in full[k]])
    json.dump(out, open("cv_summary.json", "w"), indent=1)

if __name__ == "__main__":
    main(sys.argv[1])
