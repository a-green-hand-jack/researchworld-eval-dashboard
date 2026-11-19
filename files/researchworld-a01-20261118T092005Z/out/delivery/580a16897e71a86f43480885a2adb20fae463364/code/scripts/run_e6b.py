"""E6b: robustness of E6 (first place with confidence) to the margin grid and to the definition of the margin, for the score rules.
usage: run_e6b.py OUT.csv board [shard n_shards] [ntargets=30] [nsub=60] [R=400]   board = helm | m39   (same sub-board, targets, noise and seeds as run_e6.py)
variant 'unit' : margin eps = c * sd0, sd0 = sd over R draws of A_t - A_leader on the UNBOOSTED board (the definition of run_e6.py), on the grid c = 0..4 (rows reproduce run_e6.py) and 5, 6, 8, 10, 12.
variant 'plan' : margin eps = c * sd_plan, sd_plan = sd of A_t - A_leader on the board with the plan's boost applied (fixed point: solve with eps = c*sd0, measure sd on the boosted board,
                 re-solve with eps = c*sd_plan, ... up to 4 rounds; sd_rounds is the number of rounds used), c = 1, 2, 3, 4, 5, 6, 8.
P(first) of a plan is always the Monte-Carlo share of R draws in which the target strictly beats every other model with independent noise on every cell of every model (rivals included)."""
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
SCORE = ["mean", "zmean", "median", "min"]
CU = (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0); CP = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0); ROUNDS = 4

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
sig = S.std(axis=0)
kw_of = lambda rule: dict(sigma=sig) if rule == "zmean" else {}


def noisy_scores(rule, Sb, rng):
    Z = np.clip(Sb + SE * rng.standard_normal(Sb.shape), 0, 100)
    return R_.scores(Z, rule, **kw_of(rule))


def mc(rule, Sb, t, nr, rng):
    A0 = R_.scores(Sb, rule, **kw_of(rule)).astype(float); A0[t] = -np.inf; lead = int(np.argmax(A0))
    wins = 0; d = np.empty(nr)
    for r in range(nr):
        A = noisy_scores(rule, Sb, rng).astype(float)
        d[r] = A[t] - A[lead]
        A[t] = -np.inf
        wins += (d[r] + A[lead] > A.max())
    return wins / nr, float(d.std()), lead


def solve(rule, t, eps):
    return SV.price(rule, S, t, 100.0, ceil=100.0, objective="depth", eps_agg=max(eps, SV.EPS_AGG), sigma=sig if rule == "zmean" else None, time_limit=30.0)


def boosted(t, pl):
    S2 = S.copy(); S2[t] = np.minimum(S2[t] + pl["delta"], 100.0); return S2


rows = []; t0 = time.time(); k = 0
for t in range(ntar):
    k += 1
    if (k - 1) % ns != shard: continue
    for rule in SCORE:
        rng = np.random.default_rng([SEED, t, RULES.index(rule)])
        A = R_.scores(S, rule, **kw_of(rule)).astype(float)
        p0, sd0, lead = mc(rule, S, t, NR, rng)
        base = dict(board=which, target=t, model=names[t], rule=rule, rank_rule=int((A > A[t]).sum() + 1), sd0=sd0, nsub=nsub, R=NR)
        for c in CU:                                                  # same draw order as run_e6.py: the rows with c <= 4 reproduce it
            pl = solve(rule, t, c * sd0)
            row = dict(base, variant="unit", c=c, sd_used=sd0, sd_rounds=0, feasible=bool(pl["feasible"]), depth=pl["depth"], breadth=pl["breadth"], status=pl["status"])
            row["p_first_plan"] = mc(rule, boosted(t, pl), t, NR, rng)[0] if pl["feasible"] else np.nan
            rows.append(row)
        rng2 = np.random.default_rng([SEED + 1, t, RULES.index(rule)])
        for c in CP:
            sd = sd0; pl = solve(rule, t, c * sd); rounds = 1
            while pl["feasible"] and rounds <= ROUNDS:
                _, sdn, _ = mc(rule, boosted(t, pl), t, NR, rng2)
                if abs(sdn - sd) <= 0.02 * sd: sd = sdn; break
                sd = sdn; pl = solve(rule, t, c * sd); rounds += 1
            row = dict(base, variant="plan", c=c, sd_used=sd, sd_rounds=rounds, feasible=bool(pl["feasible"]), depth=pl["depth"], breadth=pl["breadth"], status=pl["status"])
            row["p_first_plan"] = mc(rule, boosted(t, pl), t, NR, rng2)[0] if pl["feasible"] else np.nan
            rows.append(row)
    print(t, len(rows), round(time.time() - t0), flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
print("done", len(rows), round(time.time() - t0))
