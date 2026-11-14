"""Score-cap defence (external-review request #6.4b): clip every model's per-task score at a level c_t and ask who can still reach first.
Usage: python3 src/score_cap_defence.py      (writes results/analysis/score_cap_defence.csv and score_cap_defence_groups.csv)

Definition. For a rule f in {mean, median, min}, let L be the model that is first under f on the unclipped data. The organiser clips every task
at c_t = min(100, L_t + h), h in {0, 5, 10, 20} score points (h = 10 is the `gain10` increment), for ALL models and for the target:
  X'_{jt} = min(X_{jt}, c_t);   the target may raise task t from X'_{it} up to c_t (raising above c_t cannot count).
Every other model j != L stays as it is under the clip.
Second family (`clip_kind` = quantile, clip_h = q): c_t = the q-th percentile of task t over all models (a winsorisation defence that also clips
the leader); the model first under f on the clipped data is excluded as a target, the others are treated as above. The leader keeps X'_L = X_L (c >= L), so L stays first and cannot be displaced by clipping.
A target i (every model except L) `can reach first` iff min-L1 over y in [X'_i, c] is finite for the strict-first criterion (eps = 1e-3)
against max_{j != i} f(X'_j): the same exact solvers (src/mti/scorerules.py) as the unclipped analysis. h = 0 means that nobody can exceed the
leader on any task (a pure tie ceiling). The unclipped reference (ceil: everybody can reach first; gain10 cap) comes from the main results.
Strict first is impossible whenever the clip also binds on the first model on every task where the target could gain: the target can then at best tie
(`n_tasks_where_first_is_clipped` shows how often the clip binds on the first model). Also reported: the 'clip + gain10 attack' column (the target's own raise is further limited to X + 10 points, as in the gain10 scenario).
"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from scipy.stats import rankdata
from mti import scorerules as sr, data as dt
OUT = ROOT / "results" / "analysis"; EPS = 1e-3
BINS = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 500), (501, 10**6)]
lab = lambda lo, hi: f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
grp = lambda r: next((lab(lo, hi) for lo, hi in BINS if lo <= r <= hi), "1")
GROUPS = [lab(*b) for b in BINS]

def wilson(k, n, z=1.96):
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h

rows, grows = [], []
for ds in ["ollb", "helm"]:
    X, names, tasks, _ = dt.load(ds); M, n = X.shape
    mean_rank = rankdata(-X.mean(axis=1), method="min")
    for rule in ["mean", "median", "min"]:
        fv = sr.RULES[rule][0]; L = int(np.argmax(fv(X))); lead_name = names[L]
        levels = [("leader+h", h, np.minimum(X[L] + h, 100.0)) for h in (0, 5, 10, 20)] + \
                 [("quantile", q, np.percentile(X, q, axis=0)) for q in (99, 95, 90)]
        for clip_kind, h, c in levels:
            Xc = np.minimum(X, c); Lc = int(np.argmax(fv(Xc)))
            res = {}
            for attack in ["ceil", "gain10"]:
                feas = np.zeros(M, bool); L1 = np.full(M, np.nan); K = np.full(M, np.nan)
                for i in range(M):
                    if i == Lc: continue
                    cap = c if attack == "ceil" else np.minimum(c, Xc[i] + 10.0)
                    o = sr.min_investment(rule, Xc, i, cap, EPS, measures=("L1", "K"))
                    feas[i] = np.isfinite(o["L1"]); L1[i] = o["L1"] if feas[i] else np.nan; K[i] = o["K"] if feas[i] else np.nan
                res[attack] = (feas, L1, K)
                tg = np.arange(M) != Lc; k = int(feas[tg].sum()); lo, hi = wilson(k, int(tg.sum()))
                rows.append(dict(dataset=ds, rule=rule, leader=lead_name, clip_kind=clip_kind, clip_h=h, first_after_clip=names[Lc], n_tasks_where_first_is_clipped=int((X[Lc] > c + 1e-12).sum()), attack_cap=attack, n_targets=int(tg.sum()), n_can_reach_first=k,
                                 share_can_reach_first=k / tg.sum(), share_lo=lo, share_hi=hi,
                                 L1_med_feasible=float(np.nanmedian(L1[tg])) if k else np.nan, K_med_feasible=float(np.nanmedian(K[tg])) if k else np.nan,
                                 n_targets_clipped_at_start=int(((X != Xc).any(axis=1) & tg).sum()),
                                 median_points_clipped_off_target=float(np.median((X - Xc).sum(axis=1)[tg]))))
                for g in GROUPS:
                    m_ = tg & np.array([grp(r) == g for r in mean_rank])
                    if m_.any(): grows.append(dict(dataset=ds, rule=rule, clip_kind=clip_kind, clip_h=h, attack_cap=attack, group=g, n_targets=int(m_.sum()),
                                                   share_can_reach_first=float(feas[m_].mean())))
        print(ds, rule, "done", flush=True)
R = pd.DataFrame(rows); R.to_csv(OUT / "score_cap_defence.csv", index=False)
pd.DataFrame(grows).to_csv(OUT / "score_cap_defence_groups.csv", index=False)
pd.set_option("display.width", 250)
print(R[["dataset", "rule", "clip_kind", "clip_h", "attack_cap", "n_targets", "share_can_reach_first", "L1_med_feasible", "K_med_feasible", "n_targets_clipped_at_start"]].round(3).to_string())
