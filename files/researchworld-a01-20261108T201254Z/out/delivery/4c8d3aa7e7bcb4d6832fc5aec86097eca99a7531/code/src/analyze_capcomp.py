"""Composition of the empirical cap (external-review request #6.1).
Usage: python3 src/analyze_capcomp.py     (reads data/processed/ollb6.csv and results/ollb_capcomp_*.csv, ollb_score_*.csv, ollb_plurality_sample.csv)
Writes results/analysis/:
  cap_composition_pairs.csv      per subset of the declared (fine-tune, base) pairs: n pairs, per-task emp95 / emp99 / mean gain / share of headroom closed (q95)
  cap_composition_types.csv      counts of the 540 pairs by Type of the fine-tune and by Type of its base
  cap_composition_feasible.csv   share of targets that can reach first, and median L1 among those, by rule x cap x rank group
"""
import sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from mti import data as dt
R = ROOT / "results"; OUT = R / "analysis"
T = dt.OLLB_TASKS

# ---- (a) composition and per-task caps
rows = []
for sub in ["all", "chat", "nochat", "domain", "nochatname"]:
    ft, base, p = dt.empirical_pairs(sub); g = ft - base
    for t, task in enumerate(T):
        rows.append(dict(subset=sub, n_pairs=len(p), task=task, emp95=np.percentile(g[:, t], 95), emp99=np.percentile(g[:, t], 99),
                         mean_gain=g[:, t].mean(), median_gain=np.median(g[:, t]),
                         frac95=dt.empirical_frac_caps(95, sub)[0][t], share_pairs_gain_gt_10=float((g[:, t] > 10).mean())))
pd.DataFrame(rows).to_csv(OUT / "cap_composition_pairs.csv", index=False)

d = pd.read_csv(dt.PROC / "ollb6.csv"); d = d[~d.Flagged]; idx = d.drop_duplicates("fullname").set_index("fullname")
_, _, p = dt.empirical_pairs("all"); p = p.copy(); p["base_type"] = idx.loc[p["Base Model"], "Type"].values
p["chat_like_name"] = p.fullname.str.contains(dt.CHAT_NAME)
ty = p.groupby(["Type", "base_type"]).size().rename("n_pairs").reset_index()
ty["note"] = ""
ty = pd.concat([ty, pd.DataFrame([dict(Type="(all pairs)", base_type="chat-like model name (regex)", n_pairs=int(p.chat_like_name.sum()), note=f"regex {dt.CHAT_NAME.pattern}"),
                                  dict(Type="(all pairs)", base_type="Type chat or chat-like name", n_pairs=int(((p.Type == dt.CHAT) | p.chat_like_name).sum()), note=""),
                                  dict(Type="(all pairs)", base_type="neither", n_pairs=int(((p.Type != dt.CHAT) & ~p.chat_like_name).sum()), note="used for emp95_nochatname")])])
ty.to_csv(OUT / "cap_composition_types.csv", index=False)

# ---- (b,c) feasibility by rank group under each cap
BINS = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 500), (501, 10**6)]
lab = lambda lo, hi: f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
grp = lambda r: next((lab(lo, hi) for lo, hi in BINS if lo <= r <= hi), "1")
GROUPS = [lab(*b) for b in BINS]
import glob
parts = []
for f in glob.glob(str(R / "ollb_capcomp_*.csv")): parts.append(pd.read_csv(f).assign(src="capcomp"))
for cap in ["ceil", "emp95", "emp99"]:
    s = pd.read_csv(R / f"ollb_score_{cap}.csv"); parts.append(s[s.rule.isin(["mean", "median", "min"])].assign(src="main"))
pl = pd.read_csv(R / "ollb_plurality_sample.csv"); parts.append(pl[pl.cap.isin(["ceil", "emp95", "emp99"])].assign(src="main"))
D = pd.concat(parts, ignore_index=True).drop_duplicates(["cap", "rule", "target"])
D["group"] = [grp(r) for r in D.rank_mean]; D = D[D.group != "1"]
D["L1"] = pd.to_numeric(D.L1, errors="coerce")
full = pd.read_csv(R / "ollb_score_ceil.csv"); full = full[full.rule == "mean"]
pop = pd.Series([grp(r) for r in full.rank_mean]).value_counts().to_dict()
rows = []
for (cap, rule), s in D.groupby(["cap", "rule"]):
    design = "sample" if rule == "plurality" else "all"
    r_ = dict(cap=cap, rule=rule, design=design, n_targets=len(s), n_censored=int(s.censored.fillna(0).sum()))
    ok = s[s.censored.fillna(0) == 0]
    if design == "sample":     # stratum-weighted population share (weights = stratum size / sampled in stratum)
        w = ok.group.map(lambda g: pop.get(g, 0) / (ok.group == g).sum()); r_["feasible_share_all"] = float((w * ok.feasible).sum() / w.sum())
    else: r_["feasible_share_all"] = float(ok.feasible.mean())
    for g in GROUPS:
        x = ok[ok.group == g]
        r_[f"feas_{g}"] = float(x.feasible.mean()) if len(x) else np.nan
        r_[f"n_{g}"] = len(x)
        r_[f"L1med_feas_{g}"] = float(x.L1[np.isfinite(x.L1)].median()) if (np.isfinite(x.L1)).any() else np.nan
    rows.append(r_)
F = pd.DataFrame(rows).sort_values(["rule", "cap"]); F.to_csv(OUT / "cap_composition_feasible.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(pd.read_csv(OUT / "cap_composition_pairs.csv").query("subset in ['all','nochat','nochatname','chat']").pivot(index="task", columns="subset", values="emp95").round(1))
print(ty.to_string())
print(F[["rule", "cap", "feasible_share_all"] + [f"feas_{g}" for g in GROUPS]].round(3).to_string())
