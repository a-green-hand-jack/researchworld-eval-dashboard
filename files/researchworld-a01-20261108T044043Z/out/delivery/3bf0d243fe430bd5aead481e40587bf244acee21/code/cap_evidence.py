"""Evidence for the empirical gain caps (issue #10): pair bootstrap, leave-one-task-allowance-out, joint-gain description, HELM allowance sensitivity.
Usage: python3 code/cap_evidence.py OUTDIR [--draws 1000] [--seed 0]
Feasibility of a target at a cap vector c is tested at the cap-saturated vector y = c (every task raised to its cap): for a rule that is monotone in
every score (mean, median, min) the target can become first iff it is strictly first at y, i.e. f(y) >= tau + eps (tau = best rule value among the other
models, eps = 1e-3 as in the primary runs). This is exactly the closed-form feasibility test of code/mti/scorerules.py, but vectorised over targets.
Targets are all models with rank_mean >= 2 under the six-task mean (the mean leader is excluded). Rank ties follow code/run_core.py (scipy rankdata 'min').
Outputs:
  pair_bootstrap_draws.csv   one row per draw: the six emp99 caps and, per rule, feasible share / n / largest feasible mean rank / longest all-feasible prefix
  pair_bootstrap_summary.csv observed value (all 540 pairs) and 2.5/50/97.5 percentiles over draws, per rule and statistic
  loto_allowance.csv         task allowance set to zero in turn (others emp99), per rule: observed n_feasible/share/frontier + bootstrap percentiles
  joint_gains.csv            descriptive in-sample counts over the 540 pairs
  helm_transfer_sensitivity.csv  uniform allowance h (six OLLB emp99 values and gain5/10/20) on all 57 HELM subjects
"""
import sys, argparse, pathlib
import numpy as np, pandas as pd
from scipy.stats import rankdata
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mti.data as dt

ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--draws", type=int, default=1000); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args(); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
EPS = 1e-3
RULES = {"mean": lambda Y: Y.mean(-1), "median": lambda Y: np.median(Y, -1), "min": lambda Y: Y.min(-1)}


def prep(X):
    """rule value of every model, tau_i = best value among the others, and the mean-rank (>=2 targets in rank order)"""
    rk = rankdata(-X.mean(1), method="min"); tg = np.where(rk >= 2)[0]; tg = tg[np.argsort(rk[tg], kind="stable")]
    tau = {}
    for r, f in RULES.items():
        v = f(X); o = np.sort(v)[::-1]; tau[r] = np.where(v == o[0], o[1], o[0])    # best other value (o[1] if i holds the unique best)
    return rk, tg, tau


def feasible(X, tg, tau, h):
    """feasible[rule][k] for target tg[k]; h: gain allowance, (n,) or scalar"""
    C = np.minimum(X[tg] + np.maximum(h, 0), 100.0)
    return {r: RULES[r](C) >= tau[r][tg] + EPS - 1e-12 for r in RULES}


def stats(rk_t, f):
    """share, n, largest feasible rank_mean, longest all-feasible prefix (largest r with every target of rank_mean <= r feasible)"""
    bad = ~f; pre = rk_t.max() if not bad.any() else rk_t[bad.argmax()] - 1
    return dict(n_targets=len(f), n_feasible=int(f.sum()), share=f.mean(), max_feasible_rank=int(rk_t[f].max()) if f.any() else 0, prefix_rank=int(pre))


X, names, tasks, meta = dt.load("ollb")
rk, tg, tau = prep(X); rk_t = rk[tg]
G = dt._gains(); P = len(G)
caps_obs = np.percentile(G, 99, axis=0)

# ------------------------------------------------------------------ consistency with the primary run
core = pd.read_csv(pathlib.Path(__file__).resolve().parents[1] / "results" / "core_ollb.csv")
core = core[(core.cap == "emp99") & (core.rank_mean >= 2)]
obs = feasible(X, tg, tau, caps_obs)
for r in RULES:
    ref = int((core[core.rule == r].status != "infeasible").sum()); assert int(obs[r].sum()) == ref, (r, int(obs[r].sum()), ref)
print("cap-saturated test reproduces the primary feasible counts:", {r: int(obs[r].sum()) for r in RULES})

# ------------------------------------------------------------------ 1. pair bootstrap (+ 2. leave-one-task-allowance-out inside each draw)
rng = np.random.default_rng(a.seed)
draws, loto_rows = [], []
LOTO = ["none"] + tasks      # "none" = primary caps


def evaluate(caps):
    f = feasible(X, tg, tau, caps)
    return {r: stats(rk_t, f[r]) for r in RULES}


obs_all = {"none": evaluate(caps_obs)}
for k, t in enumerate(tasks):
    c = caps_obs.copy(); c[k] = 0.0; obs_all[t] = evaluate(c)
for d in range(a.draws):
    idx = rng.integers(0, P, P); cd = np.percentile(G[idx], 99, axis=0)
    row = dict(draw=d, **{f"cap_{t}": cd[k] for k, t in enumerate(tasks)})
    for lo in LOTO:
        c = cd.copy()
        if lo != "none": c[tasks.index(lo)] = 0.0
        ev = evaluate(c)
        for r in RULES:
            if lo == "none": row.update({f"{r}_{s}": v for s, v in ev[r].items() if s != "n_targets"})
            else: loto_rows.append(dict(draw=d, dropped=lo, rule=r, **{s: v for s, v in ev[r].items() if s != "n_targets"}))
    draws.append(row)
D = pd.DataFrame(draws); D.to_csv(out / "pair_bootstrap_draws.csv", index=False)
pct = lambda x: np.percentile(x, [2.5, 50, 97.5])
S = []
for r in RULES:
    for s in ("n_feasible", "share", "max_feasible_rank", "prefix_rank"):
        lo_, md, hi_ = pct(D[f"{r}_{s}"]); S.append(dict(rule=r, stat=s, observed=obs_all["none"][r][s], p2_5=lo_, p50=md, p97_5=hi_))
for k, t in enumerate(tasks):
    lo_, md, hi_ = pct(D[f"cap_{t}"]); S.append(dict(rule="all", stat=f"emp99_cap_{t}", observed=caps_obs[k], p2_5=lo_, p50=md, p97_5=hi_))
S = pd.DataFrame(S); S["draws"] = a.draws; S["seed"] = a.seed; S["n_pairs"] = P; S["n_targets"] = len(tg)
S.to_csv(out / "pair_bootstrap_summary.csv", index=False)

L = pd.DataFrame(loto_rows); R = []
for lo in tasks:
    for r in RULES:
        z = L[(L.dropped == lo) & (L.rule == r)]; o = obs_all[lo][r]; p = obs_all["none"][r]
        row = dict(dropped=lo, rule=r, cap_dropped=0.0, primary_cap=caps_obs[tasks.index(lo)], n_targets=o["n_targets"])
        for s in ("n_feasible", "share", "max_feasible_rank", "prefix_rank"):
            q = pct(z[s]); row.update({s: o[s], f"{s}_primary": p[s], f"{s}_p2_5": q[0], f"{s}_p97_5": q[2]})
        R.append(row)
pd.DataFrame(R).to_csv(out / "loto_allowance.csv", index=False)

# ------------------------------------------------------------------ 3. joint gains of the 540 pairs (descriptive, in-sample)
J = []
add = lambda k, v, note="": J.append(dict(quantity=k, value=v, note=note))
add("n_pairs", P); [add(f"emp99_cap_{t}", caps_obs[k]) for k, t in enumerate(tasks)]
add("sum_of_emp99_caps", caps_obs.sum(), "largest total gain if every task sat at its marginal cap")
for k, t in enumerate(tasks):
    add(f"n_negative_gain_{t}", int((G[:, k] < 0).sum()), "fine-tune below its base model"); add(f"n_gain_above_cap_{t}", int((G[:, k] > caps_obs[k]).sum()), "by construction ~1% of pairs")
add("n_pairs_with_any_negative_gain", int((G < 0).any(1).sum())); add("n_pairs_with_all_gains_negative_or_zero", int((G <= 0).all(1).sum()))
share_of_cap = G / caps_obs                                   # fraction of the marginal cap used on each task
for frac in (0.5, 0.9):
    cnt = (share_of_cap > frac).sum(1)
    for m in (1, 2, 3, 4, 5, 6): add(f"n_pairs_gain_gt_{frac}_cap_on_ge_{m}_tasks", int((cnt >= m).sum()), f"gain > {frac} x the task's emp99 cap")
add("n_pairs_all_six_gains_ge_cap", int((G >= caps_obs).all(1).sum()), "gain vector at or above every marginal cap simultaneously")
add("max_over_pairs_of_min_task_cap_fraction", float(share_of_cap.min(1).max()), "the pair whose weakest task reaches the largest share of its cap")
add("n_pairs_gain_gt_0.5_cap_on_ge_2_tasks_excluding_IFEval", int(((share_of_cap[:, 1:] > 0.5).sum(1) >= 2).sum()), "same count over the five non-IFEval tasks")
tot = G.sum(1); add("pair_total_gain_max", tot.max()); add("pair_total_gain_p99", np.percentile(tot, 99)); add("pair_total_gain_median", np.median(tot))
add("pair_max_task_gain_median", float(np.median(G.max(1)))); add("pair_max_task_gain_p99", float(np.percentile(G.max(1), 99)))
cr = np.corrcoef(G.T); add("mean_off_diagonal_correlation_of_task_gains", float(cr[np.triu_indices(6, 1)].mean()), "Pearson over the 540 pairs")
for i in range(6):
    for j in range(i + 1, 6): add(f"corr_{tasks[i]}_{tasks[j]}", float(cr[i, j]))
# feasibility needs a *vector* near the caps: how many pairs reach the mean-rule requirement of a typical hard target?
need = {r: (tau[r][tg] + EPS) for r in RULES}
for r in ("mean",):
    gap_mean = 6 * (tau[r][tg] + EPS) - X[tg].sum(1)          # total gain the mean rule needs
    for q in (50, 90):
        add(f"mean_rule_total_gain_needed_rank_le_{q}_median", float(np.median(gap_mean[rk_t <= q])), "total score gain needed by a target ranked <= q under the mean")
    add("pairs_with_total_gain_ge_needed_by_rank_2_target", int((tot >= gap_mean[rk_t == 2].min()).sum()), "pairs whose total gain suffices for the cheapest rank-2 target")
pd.DataFrame(J).to_csv(out / "joint_gains.csv", index=False)

# ------------------------------------------------------------------ 4. HELM: uniform allowances transferred from OLLB
XH, nh, th, _ = dt.load("helm"); rkh, tgh, tauh = prep(XH); rkh_t = rkh[tgh]
allow = {f"ollb_emp99_{t}": caps_obs[k] for k, t in enumerate(tasks)}; allow.update({f"gain{g}": float(g) for g in (5, 10, 20)})
H = []; brng = np.random.default_rng(a.seed)
bidx = brng.integers(0, len(tgh), (a.draws, len(tgh)))
for nm, h in allow.items():
    f = feasible(XH, tgh, tauh, h)
    for r in RULES:
        s = stats(rkh_t, f[r]); bs = f[r][bidx].mean(1)
        H.append(dict(allowance=nm, h=h, rule=r, **s, share_p2_5=np.percentile(bs, 2.5), share_p97_5=np.percentile(bs, 97.5),
                      note="uniform gain allowance on all 57 subjects, arbitrary transferred value" if nm.startswith("ollb") else "uniform headroom comparator"))
pd.DataFrame(H).to_csv(out / "helm_transfer_sensitivity.csv", index=False)
coreh = pd.read_csv(pathlib.Path(__file__).resolve().parents[1] / "results" / "core_helm.csv"); coreh = coreh[coreh.rank_mean >= 2]
for g in (5, 10, 20):            # the existing gain5/10/20 closed-form runs must agree with the cap-saturated test
    for r in RULES:
        ref = int((coreh[(coreh.cap == f"gain{g}") & (coreh.rule == r)].status != "infeasible").sum())
        assert ref == int(feasible(XH, tgh, tauh, float(g))[r].sum()), (g, r)
print("done", out)
