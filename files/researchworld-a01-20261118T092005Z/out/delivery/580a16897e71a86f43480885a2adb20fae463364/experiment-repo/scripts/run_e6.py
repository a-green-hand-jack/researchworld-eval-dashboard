"""E6 (Tier B): score noise. First place with confidence, and P(first) of the optimal plan by Monte Carlo.
usage: run_e6.py OUT.csv board [shard n_shards] [ntargets=30] [nsub=60] [R=400]   board = helm | m39
Sub-board: the nsub models with the highest official score (all rules are solved and simulated on this sub-board; rank rules count
wins among these models only).  Targets: the top ntargets of it.  Noise: HELM binomial sd sqrt(p(1-p)/n) per (model, subject) with
the subject's item count; OLLB the `results` stderr of each sub-task (points).  Independent Gaussian noise per cell, scores clipped to [0, 100].
For every (target, rule): P(first) of the unboosted board; the cheapest plan (uncapped, own leader, unit = points) with margin
eps_agg = c * sd(A_t - A_leader) for c = 0..4 (score rules: mean, zmean, median, min; rank rules only c = 0), and the
Monte-Carlo P(first) of each plan (boost applied to the true score, noise added to every cell)."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice import rules as R_, solvers as SV
from lbprice.boards import load_helm, load_ollb, DP

out, which = sys.argv[1], sys.argv[2]
shard, ns = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
ntar = int(sys.argv[5]) if len(sys.argv) > 5 else 30
nsub = int(sys.argv[6]) if len(sys.argv) > 6 else 60
NR = int(sys.argv[7]) if len(sys.argv) > 7 else 400
SEED = 20260301
RULES = ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"]
SCORE = {"mean", "zmean", "median", "min"}

if which == "helm":
    b = load_helm(); S_all = b["S"]
    p = np.clip(S_all / 100.0, 0.005, 0.995); SE_all = 100.0 * np.sqrt(p * (1 - p) / b["n_eval"][None, :])
    names = b["names"]
else:
    b = load_ollb("m39"); S_all = b["S"]; names = b["names"]
    se = pd.read_csv(os.path.join(DP, "ollb_sub_se.csv")).set_index("eval_name")
    SE_all = se.loc[b["meta"].eval_name.values, b["tasks"]].values.astype(float)
top = np.argsort(-b["official"], kind="stable")[:nsub]
S, SE = S_all[top], SE_all[top]; names = [names[i] for i in top]
sig = S.std(axis=0); m = S.shape[1]
kw_of = lambda rule: dict(sigma=sig) if rule == "zmean" else {}


def noisy_scores(rule, Sb, rng):
    Z = np.clip(Sb + SE * rng.standard_normal(Sb.shape), 0, 100)
    return R_.scores(Z, rule, **kw_of(rule))


def mc(rule, Sb, t, nr, rng):
    """P(t strictly first), and sd of A_t - A_leader (leader = best other model under the noise-free scores) over nr draws."""
    A0 = R_.scores(Sb, rule, **kw_of(rule)).astype(float); A0[t] = -np.inf; lead = int(np.argmax(A0))
    wins = 0; d = np.empty(nr)
    for r in range(nr):
        A = noisy_scores(rule, Sb, rng).astype(float)
        d[r] = A[t] - A[lead]
        A[t] = -np.inf
        wins += (d[r] + A[lead] > A.max())
    return wins / nr, float(d.std()), lead


rows = []; t0 = time.time(); k = 0
for t in range(ntar):
    k += 1
    if (k - 1) % ns != shard: continue
    for rule in RULES:
        rng = np.random.default_rng([SEED, t, RULES.index(rule)])
        A = R_.scores(S, rule, **kw_of(rule)).astype(float)
        p0, sd, lead = mc(rule, S, t, NR, rng)
        base = dict(board=which, target=t, model=names[t], rule=rule, rank_rule=int((A > A[t]).sum() + 1), gap0=float(np.delete(A, t).max() - A[t]),
                    sd_diff=sd, z0=(float(np.delete(A, t).max() - A[t]) / sd if sd > 0 else np.nan), p_first_unboosted=p0, nsub=nsub, R=NR)
        for c in ((0.0, 1.0, 2.0, 3.0, 4.0) if rule in SCORE else (0.0,)):
            ts = time.time()
            pl = SV.price(rule, S, t, 100.0, ceil=100.0, objective="depth", eps_agg=max(c * sd, SV.EPS_AGG), sigma=sig if rule == "zmean" else None, time_limit=30.0)
            row = dict(base, c=c, feasible=bool(pl["feasible"]), depth=pl["depth"], breadth=pl["breadth"], verified=pl.get("verified"), status=pl["status"])
            if pl["feasible"]:
                S2 = S.copy(); S2[t] = np.minimum(S2[t] + pl["delta"], 100.0)
                row["p_first_plan"], _, _ = mc(rule, S2, t, NR, rng)
            else:
                row["p_first_plan"] = np.nan
            row["seconds"] = time.time() - ts
            rows.append(row)
    print(t, len(rows), round(time.time() - t0), flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
print("done", len(rows), round(time.time() - t0))
