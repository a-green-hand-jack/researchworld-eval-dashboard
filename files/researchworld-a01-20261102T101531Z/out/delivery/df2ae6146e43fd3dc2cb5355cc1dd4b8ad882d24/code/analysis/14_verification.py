"""C1 verification.  (a) real instances: for the arithmetic mean, closed form
  G_min = n * (incumbent mean - target mean)   (points, strict inequality: infimum)
  k_min = smallest k with  sum of the k largest per-task max boosts u_j  >  n*gap
against the solver (V.min_k / V.g_min), plus an independent check with the reference rule R.is_first:
the boost set returned by the solver makes the target strictly first, boosting G+eps points greedily on the
largest-headroom tasks makes it first and G-eps does not.
(b) small random instances with ties (m 3-11, n 3-9): every rule, solver forced onto its non-enumeration path
(closed form / greedy / MILP, enum_max=0) against brute force over all task subsets.
  python 14_verification.py -> results/verification.csv"""
from grid import *
rows = []
def mean_formula(s, S, t, delta, hi):
    n = len(s); sc = S.mean(1); gap = np.delete(sc, t).max() - sc[t]
    u = np.maximum(np.minimum(delta, hi - s), 0); need = n * gap
    if need < 0: return 0, 0.0, u
    cs = np.cumsum(np.sort(u)[::-1])
    k = int(np.argmax(cs > need + 1e-12) + 1) if (cs > need + 1e-12).any() else np.inf
    return k, (need if np.isfinite(k) else np.inf), u
def real(board, S, names, tg, tag):
    best = S.max(0)
    for t in tg:
        s = S[t]
        for gm in ["G1", "G2_0.25", "G2_0.5", "G1_add10", "ceil"]:
            delta, hi, h = gain_vectors(s, best, gm)
            kf, gf, u = mean_formula(s, S, t, delta, hi)
            res = V.min_k(S, t, "mean", delta, hi, return_set=True)
            ks, T = (res if isinstance(res, tuple) else (np.inf, np.array([], int)))
            gs = V.g_min(S, t, "mean", u, np.ones(S.shape[1])); gs = 0.0 if kf == 0 else gs
            # applied checks
            ok_set = True
            if np.isfinite(ks):
                X = S.copy(); X[t, T] = s[T] + u[T]; ok_set = bool(R.is_first(X, t, "mean")) if ks > 0 else bool(R.is_first(S, t, "mean"))
            ok_G = True
            if np.isfinite(gf) and gf > 0:
                for eps, want in [(1e-6, True), (-1e-6, False)]:
                    X = S.copy(); left = gf + eps
                    for j in np.argsort(-u):
                        a = min(u[j], max(left, 0)); X[t, j] += a; left -= a
                    ok_G &= (bool(R.is_first(X, t, "mean")) == want)
            kw = dict(leaderboard=tag["leaderboard"], granularity=tag["granularity"], gain_model=gm, target_id=names[t], rule="mean", instance_type="real")
            rows.append(dict(kw, metric="k_min", formula_value=kf, search_value=ks, abs_diff=abs(kf - ks) if np.isfinite(kf) or np.isfinite(ks) else 0.0,
                             match=int(kf == ks), applied_check=int(ok_set)))
            rows.append(dict(kw, metric="G_min", formula_value=gf, search_value=gs, abs_diff=abs(gf - gs) if np.isfinite(gf) and np.isfinite(gs) else (0.0 if gf == gs else np.inf),
                             match=int((gf == gs) or abs(gf - gs) < 1e-6), applied_check=int(ok_G)))
df = load_helm(); real("helm", df.values, df.index.values, np.arange(len(df)), dict(leaderboard="helm_mmlu", granularity="headline"))
o, S = load_olb("main"); tg, _ = pick_targets(S, 300)
real("olb", S, o["fullname"].values, tg, dict(leaderboard="openllm_v2", granularity="headline"))
sub = pd.read_csv(f"{ROOT}/data/processed/olb_subtask.csv", index_col=0); tg2, _ = pick_targets(sub.values, 150)
real("olb", sub.values, sub.index.values, tg2, dict(leaderboard="openllm_v2", granularity="subtask"))
# (b) small instances
rng = np.random.default_rng(31415); small = []
for _ in range(400):
    m = int(rng.integers(3, 12)); n = int(rng.integers(3, 10))
    S = np.clip(rng.normal(50, 15, (m, 1)) + rng.normal(0, 12, (m, n)), 0, 100).round(0)
    t = int(rng.integers(m)); d = float(rng.choice([5, 15, 40, 100, np.inf])); hi = 100.0 if rng.random() < .5 else np.minimum(100, S.max(0) + 1)
    for rule in R.ALL_RULES:
        a = V.min_k(S, t, rule, d, hi, enum_max=0); b = V._enum_min_k(S, t, rule, d, hi)
        small.append((rule, int(a == b), (a - b) if np.isfinite(a) and np.isfinite(b) else (0 if a == b else np.inf)))
sm = pd.DataFrame(small, columns=["rule", "match", "diff"])
for rule, g in sm.groupby("rule", sort=False):
    rows.append(dict(leaderboard="synthetic_small", granularity="n3-9", gain_model="mixed", target_id=f"{len(g)} instances", rule=RULE_META[rule][0],
                     rule_param=RULE_META[rule][1], instance_type="small_exhaustive", metric="k_min", formula_value=np.nan, search_value=np.nan,
                     abs_diff=float(g["diff"].abs().max()), match=int(g.match.all()), n_instances=len(g), n_match=int(g.match.sum()),
                     max_excess=float(g["diff"].max())))
out = pd.DataFrame(rows); out.to_csv(f"{ROOT}/results/verification.csv", index=False)
r = out[out.instance_type == "real"]; print(r.groupby(["leaderboard", "granularity", "metric"]).agg(n=("match", "size"), match=("match", "mean"), applied=("applied_check", "mean"), maxdiff=("abs_diff", "max")))
print(out[out.instance_type == "small_exhaustive"][["rule", "rule_param", "n_instances", "n_match", "max_excess"]])
