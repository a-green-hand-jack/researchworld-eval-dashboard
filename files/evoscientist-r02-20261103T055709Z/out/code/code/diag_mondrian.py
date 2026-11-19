"""Diagnostic: why does Mondrian-on-confidence-bins over-cover (0.905 vs 0.901)?
Compare realised coverage to the exact expectation sum_g P(g) (n_g+1-l_g)/(n_g+1) given the realised group sizes.
Usage: python code/diag_mondrian.py -> results/diag_mondrian.csv"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "code")
import cp, exp_synth as E
rows = []
for (K, k0) in [(3, 30), (10, 30), (10, 300)]:
    for rep in range(100):
        rng = np.random.default_rng([999, K, int(k0), rep]); B, C = cp.scenario_params(K)
        n = E.NTR + E.NCAL + E.NREF + E.NEV
        x, y, _ = cp.gen_data(rng, n, K, k0, 0, 0, B=B, C=C)
        tr, cal, ref, ev = np.split(np.arange(n), np.cumsum([E.NTR, E.NCAL, E.NREF]))
        P = cp.fit_softmax_reg(x[tr], y[tr])(x); conf = P.max(1)
        edges = np.quantile(conf[tr], np.linspace(0, 1, 6)[1:-1]); g = np.searchsorted(edges, conf, side="right")
        f = cp.make_score("l2"); s = f(y, P)
        q = cp.mondrian_quantiles(s[cal], g[cal], g[ev], 0.1)
        exp = 0.0
        for b in range(5):
            ng = (g[cal] == b).sum(); pg = (g[ev] == b).mean(); l = int(np.floor((ng + 1) * 0.1))
            exp += pg * ((ng + 1 - l) / (ng + 1))
        rows.append(dict(K=K, kappa0=k0, rep=rep, cov=(s[ev] <= q).mean(), expected=exp, min_ng=min((g[cal] == b).sum() for b in range(5))))
d = pd.DataFrame(rows); out = d.groupby(["K", "kappa0"]).agg(cov=("cov", "mean"), cov_se=("cov", "sem"), expected=("expected", "mean"), min_ng=("min_ng", "mean")).round(4)
print(out); out.to_csv("results/diag_mondrian.csv")
