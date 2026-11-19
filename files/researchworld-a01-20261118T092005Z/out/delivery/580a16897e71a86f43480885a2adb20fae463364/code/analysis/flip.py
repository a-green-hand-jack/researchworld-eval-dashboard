"""Why does the breadth ordering of the rule classes flip between boards?  (R1 diagnostic, request experiment-repo#6; descriptive, post hoc.)
usage: flip.py TABLES_DIR RAWDIR   reads RAWDIR/r1_*.csv (breadth at b = c x median B* of the mean family, sigma units; c = 1 used here) and the boards; writes TABLES_DIR/flip_profile.csv, flip_summary.csv, flip_proxy.csv.
Per board (HELM m=57, OLLB benchmark level m=6 'm6raw', OLLB sub-tasks m=39) and per top-30 target t, against the official leader l (the runner-up if t leads), with d_j = (S[l,j] - S[t,j]) / sigma_j:
  ahead / near        share of tasks where t >= l / where the deficit is <= 1 sigma
  D, dmed, dmax       sum, median (over tasks where t is behind) and maximum of the positive deficits in sigma
  need_med, marg_med  the median functional: tasks t must lift above l's median level M_l (share of m) and the largest of the shortfalls to M_l it must close there (sigma)
  need_plur, marg_plur  plurality: tasks t must win outright to have strictly more outright wins than every rival (greedy, see plur_greedy; an upper bound on the minimum) as a share of m, and the largest sigma-gap to the current best score among them
  cop_def             Copeland: (score of the best rival - score of t) / (N - 1)
  k_*_proxy           breadth lower bound of each rule from the profile alone at the R1 cap b sigma per task (against l only): mean = fewest tasks whose caps b sigma_j (x weight) cover the aggregate gap; median = need_med if marg_med <= b else infeasible;
                      plurality = the same greedy restricted to tasks within b (infeasible if it cannot finish); infeasible counts as k/m = 1 as in R1.
Outcome: R1 breadth k/m at c = 1 (infeasible = 1); delta = k/m(rule) - k/m(mean reference: mean, or the hierarchical mean on m=39).  deltaBF = delta over the targets feasible for both rules (NaN otherwise).  Summary: medians per board with cluster (family) bootstrap CI; association (Spearman) of proxy and
outcome pooled and within board."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import warnings; warnings.filterwarnings("ignore", category=RuntimeWarning)
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from lbprice.boards import load_helm, load_ollb
from lbprice import rules as R
from families import fam_map
T, RAW = sys.argv[1], sys.argv[2]; NB = int(os.environ.get("NBOOT", 2000))
BOARD = {"helm": "helm_mmlu", "m6raw": "ollb_bench_raw", "m39": "ollb_sub"}
MEDT = ["median", "plurality", "copeland"]


def kmean_proxy(S, t, l, sig, w, b):
    """fewest tasks whose caps (b sigma_j, weighted) cover the weighted aggregate gap to l"""
    gap = float(w @ (S[l] - S[t]))
    if gap <= 0: return 0
    gains = np.sort(w * b * sig)[::-1].cumsum()
    k = int(np.searchsorted(gains, gap, side="left")) + 1
    return k if k <= len(gains) else np.inf


def plur_greedy(P, owner, own, cost, t, cap):
    """Tasks t must win to have strictly more outright wins than every rival (greedy; an upper bound on the minimum): repeatedly take the cheapest task (cost <= cap) held by a rival
    whose count is currently the maximum, else the cheapest task held by anybody or by nobody.  Returns (number of tasks, largest sigma-cost used); (inf, nan) if the cap makes it impossible."""
    cnt = P.copy(); owned = own.copy(); ow = owner.copy(); used = []; taken = np.zeros(len(cost), bool)
    cnt_t = cnt[t]; mine = owned & (ow == t); taken |= mine
    while True:
        rival = np.where(np.arange(len(cnt)) == t, -1, cnt); mx = rival.max()
        if cnt[t] > mx: return float(len(used)), (max(used) if used else 0.0)
        cand = np.flatnonzero(~taken & (cost <= cap))
        if not len(cand): return np.inf, np.nan
        top_r = np.flatnonzero(rival == mx); sw = [j for j in cand if owned[j] and ow[j] in top_r]
        j = min(sw, key=lambda j: cost[j]) if sw else min(cand, key=lambda j: cost[j])
        taken[j] = True; used.append(cost[j]); cnt[t] += 1
        if owned[j]: cnt[ow[j]] -= 1; owned[j] = False


rows = []
for name in ("helm", "m6raw", "m39"):
    bd, fam = fam_map(name); S = bd["S"]; N, m = S.shape; sig = S.std(0); off = bd["official"]; order = np.argsort(-off, kind="stable")
    w = bd["w_h"] if name == "m39" else np.full(m, 1.0 / m)
    r1 = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{RAW}/r1_{name}*.csv")) if "r1x" not in f])
    r1 = r1[(r1.c == 1.0) & (r1.objective == "breadth")].drop_duplicates(["target", "rule"]); b = float(r1.b_sigma.iloc[0])
    r1["kf"] = np.where(r1.feasible, r1.k / r1.m, 1.0)
    K = r1.pivot_table(index="target", columns="rule", values="kf"); F = r1.pivot_table(index="target", columns="rule", values="feasible")
    ref = "meanh" if name == "m39" else "mean"
    top = S.max(0); own = (S == top).sum(0) == 1; owner = S.argmax(0)
    P = np.array([(own & (owner == i)).sum() for i in range(N)], float); C = R.copeland_cached(S)
    for t in sorted(r1.target.unique()):
        l = order[0] if order[0] != t else order[1]
        d = (S[l] - S[t]) / sig; pos = np.clip(d, 0, None)
        Ml = np.median(S[l]); sh = (Ml - S[t]) / sig; need = max(0, (m + 1) // 2 - int((S[t] > Ml).sum())); shs = np.sort(sh[sh > 0])
        marg_med = float(shs[need - 1]) if 0 < need <= len(shs) else 0.0
        cost_t = (top - S[t]) / sig                                                    # sigma needed to reach the current best score on each task
        npl, marg_plur = plur_greedy(P, owner, own, cost_t, t, np.inf)
        kpl = plur_greedy(P, owner, own, cost_t, t, b)[0]
        kmed = need if marg_med <= b else np.inf
        km = kmean_proxy(S, t, l, sig, w, b)
        f = lambda k: 1.0 if not np.isfinite(k) else k / m
        npl = npl if np.isfinite(npl) else np.nan
        row = dict(board=BOARD[name], m=m, target=int(t), family=fam[bd["names"][t]], b_sigma=b, ahead=float((d <= 0).mean()), near=float((d <= 1).mean()), D=float(pos.sum()), dmed=float(np.median(pos[pos > 0])) if (pos > 0).any() else 0.0,
                   dmax=float(pos.max()), need_med=need / m, marg_med=marg_med, need_plur=npl / m, marg_plur=marg_plur, cop_def=float((C.max() - C[t]) / (N - 1)),
                   k_mean_proxy=f(km), k_median_proxy=f(kmed), k_plurality_proxy=f(kpl))
        for rule in ["mean", "zmean", "median", "min", "borda", "plurality", "copeland"] + (["meanh"] if name == "m39" else []):
            row[f"kf_{rule}"] = float(K.loc[t, rule]); row[f"feas_{rule}"] = bool(F.loc[t, rule])
        row["ref"] = ref
        for rule in MEDT: row[f"deltaBF_{rule}"] = row[f"kf_{rule}"] - row[f"kf_{ref}"] if (row[f"feas_{rule}"] and row[f"feas_{ref}"]) else np.nan   # jointly feasible targets only
        for rule in MEDT: row[f"delta_{rule}"] = row[f"kf_{rule}"] - row[f"kf_{ref}"]
        rows.append(row)
P_ = pd.DataFrame(rows); P_.to_csv(f"{T}/flip_profile.csv", index=False)


def med_ci(x, fam, seed):
    x = np.asarray(x, float); lab = pd.factorize(np.asarray(fam))[0]; k = lab.max() + 1; g = [np.flatnonzero(lab == c) for c in range(k)]
    rng = np.random.default_rng(seed); bs = [np.nanmedian(x[np.concatenate([g[c] for c in rng.integers(0, k, k)])]) for _ in range(NB)]
    return float(np.nanmedian(x)), float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))


S_ = []
cols = ["ahead", "near", "D", "dmed", "dmax", "need_med", "marg_med", "need_plur", "marg_plur", "cop_def", "k_mean_proxy", "k_median_proxy", "k_plurality_proxy",
        "kf_mean", "kf_median", "kf_plurality", "kf_copeland", "delta_median", "delta_plurality", "delta_copeland", "deltaBF_median", "deltaBF_plurality", "deltaBF_copeland"]
for (bn, g) in P_.groupby("board"):
    for c in cols:
        est = med_ci(g[c].values, g.family.values, 17)
        S_.append(dict(board=bn, m=int(g.m.iloc[0]), b_sigma=float(g.b_sigma.iloc[0]), quantity=c, median=est[0], ci_lo=est[1], ci_hi=est[2], n_targets=len(g), n_families=g.family.nunique(),
                       share_nan=float(g[c].isna().mean())))
    for rule in ["median", "plurality", "copeland"]:
        S_.append(dict(board=bn, m=int(g.m.iloc[0]), b_sigma=float(g.b_sigma.iloc[0]), quantity=f"share_feasible_{rule}", median=float(g[f"feas_{rule}"].mean()), ci_lo=np.nan, ci_hi=np.nan, n_targets=len(g), n_families=g.family.nunique(), share_nan=0.0))
    S_.append(dict(board=bn, m=int(g.m.iloc[0]), b_sigma=float(g.b_sigma.iloc[0]), quantity="share_feasible_ref", median=float(np.mean([g.loc[i, f"feas_{r}"] for i, r in zip(g.index, g.ref)])), ci_lo=np.nan, ci_hi=np.nan, n_targets=len(g), n_families=g.family.nunique(), share_nan=0.0))
pd.DataFrame(S_).to_csv(f"{T}/flip_summary.csv", index=False)

# does the profile proxy reproduce the outcome?  (proxy k/m vs R1 k/m; agreement of the sign of the median-type minus mean difference)
A = []
P_["kf_ref"] = np.where(P_.ref == "meanh", P_.kf_meanh, P_.kf_mean); P_["feas_ref"] = np.where(P_.ref == "meanh", P_.feas_meanh.fillna(False), P_.feas_mean).astype(bool)
for rule, px in (("ref", "k_mean_proxy"), ("median", "k_median_proxy"), ("plurality", "k_plurality_proxy")):
    for bn, g in list(P_.groupby("board")) + [("pooled", P_)]:
        kp = g[px] - g.k_mean_proxy; ko = g[f"delta_{rule}"] if rule != "ref" else g.kf_ref - g.kf_ref
        rho = spearmanr(g[px], g[f"kf_{rule}"]).statistic if g[px].nunique() > 1 and g[f"kf_{rule}"].nunique() > 1 else np.nan
        rho_d = spearmanr(kp, ko).statistic if kp.nunique() > 1 and ko.nunique() > 1 and rule != "ref" else np.nan
        sg = (np.sign(kp.round(6)) == np.sign(ko.round(6))) if rule != "ref" else pd.Series(np.nan, index=g.index)
        mae = float((g[px] - g[f"kf_{rule}"]).abs().median())
        A.append(dict(rule=rule, board=bn, n_targets=len(g), spearman_k=rho, spearman_delta=rho_d, sign_agreement=float(sg.mean()), median_abs_err_k=mae,
                      proxy_share_infeasible=float((g[px] >= 1).mean()), actual_share_infeasible=float((~g[f"feas_{rule}"]).mean())))
pd.DataFrame(A).to_csv(f"{T}/flip_proxy.csv", index=False)
pd.set_option("display.width", 250)
print(pd.DataFrame(S_).pivot_table(index="quantity", columns="board", values="median").round(2).to_string())
print(pd.DataFrame(A).round(2).to_string())

# ---- is the plurality margin an effect of the number of models N?  Random subsets of the models (the 30 targets always kept) at the board's own b: margin to the task-best score and share feasible.
NS = {"helm": (30, 45, 60, 79), "m6raw": (30, 60, 120, 250, 500, 1000, 2000), "m39": (30, 60, 120, 250, 500, 1000, 2000)}
NR = int(os.environ.get("NDRAW", 20)); NR_ = []
for name in ("helm", "m6raw", "m39"):
    bd, _ = fam_map(name); S0 = bd["S"]; Nfull, m = S0.shape; sig = S0.std(0); tg = sorted(P_[P_.board == BOARD[name]].target.unique()); b = float(P_[P_.board == BOARD[name]].b_sigma.iloc[0])
    for n in [x for x in NS[name] if x < Nfull] + [Nfull]:
        for dr in range(NR if n < Nfull else 1):
            rng = np.random.default_rng([20260501, n, dr]); others = np.setdiff1d(np.arange(Nfull), tg)
            keep = np.concatenate([tg, rng.choice(others, n - len(tg), replace=False)]) if n < Nfull else np.arange(Nfull)
            S = S0[keep]; top = S.max(0); own = (S == top).sum(0) == 1; owner = S.argmax(0); P = np.array([(own & (owner == i)).sum() for i in range(len(S))], float)
            tl = np.flatnonzero(np.isin(keep, tg)); mg, fe = [], []
            for t in tl:
                cost = (top - S[t]) / sig
                _, mp = plur_greedy(P, owner, own, cost, t, np.inf); kk = plur_greedy(P, owner, own, cost, t, b)[0]
                mg.append(mp); fe.append(np.isfinite(kk))
            NR_.append(dict(board=BOARD[name], N=n, draw=dr, b_sigma=b, median_marg_plur=float(np.nanmedian(mg)), share_feasible_plur=float(np.mean(fe))))
pd.DataFrame(NR_).to_csv(f"{T}/flip_N.csv", index=False)
print(pd.DataFrame(NR_).groupby(["board", "N"])[["median_marg_plur", "share_feasible_plur"]].mean().round(2).to_string())
