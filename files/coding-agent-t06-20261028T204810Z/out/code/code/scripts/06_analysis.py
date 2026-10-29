"""Builds every table (paper/tables/*.tex) and summary number (results/summary.json)
from the outputs of scripts 00-05.  Figures are made by 07_figures.py."""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lbstab.prep import LLM_SETS, NBA_SEASONS
from lbstab import data as D

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
RES = os.path.join(ROOT, "results")
TAB = os.path.join(ROOT, "paper", "tables")
os.makedirs(TAB, exist_ok=True)
KINDS = ("drop", "flip", "inject")
NBA = [f"nba{s}" for s in NBA_SEASONS]
PRETTY = {"arena55k": "Arena-55k", "arena140k": "Arena-140k", "webdev10k": "WebDev-10k",
          "mtbench_human": "MT-Bench (experts)", "mtbench_gpt4": "MT-Bench (GPT-4)",
          "arenaST_human": "Arena-ST (crowd)"}
for j in D.JUDGES:
    PRETTY["arenaST_" + j] = "Arena-ST (" + j.replace("-Instruct", "").replace("Meta-", "").replace("-v0.1", "") + ")"
SUMMARY = {}


def load_budgets(name):
    r = pd.read_parquet(os.path.join(RES, "budgets", name + ".parquet"))
    m = json.load(open(os.path.join(RES, "budgets", name + ".meta.json")))
    r["ds"] = name
    r["design"] = D.design_of(name)
    r["N"] = m["n"]
    r["nh"] = r.n_i * r.n_j / (r.n_i + r.n_j)
    return r, m


def fmt_k(k, n):
    if not np.isfinite(k):
        return "--"
    pct = 100 * k / n
    p = f"{pct:.2g}" if pct < 10 else f"{pct:.0f}"
    if "e" in p:
        p = f"{pct:.3f}"
    return f"{int(k)} ({p}\\%)"


def top_budgets(r, m):
    """top-1: min over challengers of budget(leader, j); top-5 set: min over i in
    top5, j outside."""
    out = {}
    for kind in KINDS:
        col = f"k_{kind}"
        out[f"top1_{kind}"] = r.loc[r.rank_i == 0, col].min()
        if m["m"] >= 8:
            out[f"top5_{kind}"] = r.loc[(r.rank_i < 5) & (r.rank_j >= 5), col].min()
        else:
            out[f"top5_{kind}"] = np.nan
    lead = r[(r.rank_i == 0) & (r.rank_j == 1)].iloc[0]
    out["top1_z"] = lead.z
    out["top1_names"] = (m["names"][int(lead.i)], m["names"][int(lead.j)])
    return out


# ------------------------------------------------------------------ Table 1 + 2
all_r, metas = [], {}
for nm in LLM_SETS + NBA:
    if not os.path.exists(os.path.join(RES, "budgets", nm + ".parquet")):
        continue
    r, m = load_budgets(nm)
    all_r.append(r)
    metas[nm] = m
R = pd.concat(all_r, ignore_index=True)
R.to_parquet(os.path.join(RES, "all_pairs.parquet"))

rows = []
for nm in LLM_SETS:
    if nm not in metas:
        continue
    m = metas[nm]
    r = R[R.ds == nm]
    tb = top_budgets(r, m)
    sig = r[r.z > 1.96]
    adj = r[(r.rank_j == r.rank_i + 1)]
    rows.append(dict(ds=nm, design=D.design_of(nm), n=m["n"], m=m["m"], tie=m["tie_rate"],
                     cover=(r.n_ij > 0).mean(),
                     med_n=np.median(m["counts"]), **tb,
                     frac_adj_sig=(adj.z > 1.96).mean(),
                     sig_drop_med_pct=100 * (sig.k_drop / m["n"]).median() if len(sig) else np.nan,
                     sig_frac_le_01=(sig.k_drop <= 0.001 * m["n"]).mean() if len(sig) else np.nan,
                     sig_frac_le_1=(sig.k_drop <= 0.01 * m["n"]).mean() if len(sig) else np.nan))
# NBA aggregated over seasons
nba_rows = []
for nm in NBA:
    if nm not in metas:
        continue
    m = metas[nm]
    r = R[R.ds == nm]
    tb = top_budgets(r, m)
    sig = r[r.z > 1.96]
    adj = r[(r.rank_j == r.rank_i + 1)]
    nba_rows.append(dict(ds=nm, design="sports", n=m["n"], m=m["m"], tie=0.0,
                         cover=(r.n_ij > 0).mean(), med_n=np.median(m["counts"]), **tb,
                         frac_adj_sig=(adj.z > 1.96).mean(),
                         sig_drop_med_pct=100 * (sig.k_drop / m["n"]).median() if len(sig) else np.nan,
                         sig_frac_le_01=(sig.k_drop <= 0.001 * m["n"]).mean() if len(sig) else np.nan,
                         sig_frac_le_1=(sig.k_drop <= 0.01 * m["n"]).mean() if len(sig) else np.nan,
                         eta=m["eta"]))
T = pd.DataFrame(rows)
TN = pd.DataFrame(nba_rows)
T.to_csv(os.path.join(RES, "table_headline.csv"), index=False)
TN.to_csv(os.path.join(RES, "table_nba_seasons.csv"), index=False)

with open(os.path.join(TAB, "datasets.tex"), "w") as f:
    for _, x in T.iterrows():
        f.write(f"{PRETTY[x.ds]} & {x.design} & {int(x.n):,} & {x.m} & {x.tie:.2f} & {x.cover:.2f} & {int(x.med_n):,} \\\\\n")
    if len(TN):
        f.write(f"NBA seasons 1980--2015 ({len(TN)}) & sports & {int(TN.n.median()):,} & {int(TN.m.median())} & 0 & 1.00 & {int(TN.med_n.median())} \\\\\n")

with open(os.path.join(TAB, "headline.tex"), "w") as f:
    for _, x in T.iterrows():
        cells = [PRETTY[x.ds], f"{x.top1_z:.2f}"] + [fmt_k(x[f"top1_{k}"], x.n) for k in KINDS] + \
                [fmt_k(x["top5_drop"], x.n) if np.isfinite(x["top5_drop"]) else "--",
                 f"{x.sig_drop_med_pct:.2g}\\%" if np.isfinite(x.sig_drop_med_pct) else "--",
                 f"{100*x.sig_frac_le_1:.0f}\\%" if np.isfinite(x.sig_frac_le_1) else "--"]
        f.write(" & ".join(cells) + " \\\\\n")
    if len(TN):
        def med_iqr(col, pct=False):
            v = TN[col] / TN.n * 100 if pct else TN[col]
            return v.median(), v.quantile(.25), v.quantile(.75)
        cells = [f"NBA (median of {len(TN)})", f"{TN.top1_z.median():.2f}"]
        for k in KINDS:
            mk, lo, hi = med_iqr(f"top1_{k}")
            cells.append(f"{mk:.0f} [{lo:.0f}--{hi:.0f}]")
        mk, lo, hi = med_iqr("top5_drop")
        cells += [f"{mk:.0f} [{lo:.0f}--{hi:.0f}]", f"{TN.sig_drop_med_pct.median():.2g}\\%",
                  f"{100*TN.sig_frac_le_1.median():.0f}\\%"]
        f.write(" & ".join(cells) + " \\\\\n")

# ------------------------------------------------------------------ fragility law
P = R[(R.z > 0.25) & np.isfinite(R.k_drop) & (R.k_drop >= 1)].copy()
law = {}
lawrows = []


def ols(y, X):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ b
    r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return b, r2, pred


rng = np.random.default_rng(0)
for kind in KINDS:
    Q = P[np.isfinite(P[f"k_{kind}"])]
    y = np.log(Q[f"k_{kind}"].values)
    X = np.c_[np.ones(len(Q)), np.log(Q.z.values), np.log(Q.nh.values)]
    b, r2, pred = ols(y, X)
    # cluster bootstrap over datasets (NBA seasons pooled as one cluster each season)
    groups = Q.ds.values
    ug = np.unique(groups)
    idx = {g: np.where(groups == g)[0] for g in ug}
    bs = []
    for _ in range(500):
        pick = rng.choice(ug, len(ug), replace=True)
        ii = np.concatenate([idx[g] for g in pick])
        bb, _, _ = ols(y[ii], X[ii])
        bs.append(bb)
    bs = np.array(bs)
    # closed-form predictor k_hat = z*sqrt(nh) (no fitted constants)
    khat = Q.z.values * np.sqrt(Q.nh.values) * (0.5 if kind == "flip" else 1.0)
    ratio = Q[f"k_{kind}"].values / khat
    # design effect: add design dummies
    des = pd.get_dummies(Q.design).astype(float)
    des = des.drop(columns=["crowd"])
    X2 = np.c_[X, des.values]
    b2, r2b, _ = ols(y, X2)
    law[kind] = dict(b=b.tolist(), ci=np.percentile(bs, [2.5, 97.5], axis=0).tolist(), r2=r2, n=len(Q),
                     ratio_median=float(np.median(ratio)), ratio_q10=float(np.quantile(ratio, .1)),
                     ratio_q90=float(np.quantile(ratio, .9)),
                     within2x=float(np.mean((ratio > 0.5) & (ratio < 2))),
                     design_cols=list(des.columns), b_design=b2.tolist(), r2_design=r2b)
    lawrows.append((kind, b, np.percentile(bs, [2.5, 97.5], axis=0), r2, len(Q), ratio, r2b, b2, list(des.columns)))
SUMMARY["law"] = law
with open(os.path.join(TAB, "law.tex"), "w") as f:
    for kind, b, ci, r2, n, ratio, r2b, b2, dcols in lawrows:
        f.write(f"{kind} & {b[1]:.2f} [{ci[0][1]:.2f}, {ci[1][1]:.2f}] & {b[2]:.2f} [{ci[0][2]:.2f}, {ci[1][2]:.2f}] & "
                f"{np.exp(b[0]):.2f} & {r2:.3f} & {np.median(ratio):.2f} [{np.quantile(ratio,.1):.2f}, {np.quantile(ratio,.9):.2f}] & "
                f"{r2b:.3f} & {n:,} \\\\\n")

# per-design ratio summaries (k / (z sqrt(nh)))
P["C_drop"] = P.k_drop / (P.z * np.sqrt(P.nh))
P["C_inject"] = P.k_inject / (P.z * np.sqrt(P.nh))
P["C_flip"] = P.k_flip / (P.z * np.sqrt(P.nh))
SUMMARY["C_by_ds"] = P.groupby("ds")[["C_drop", "C_flip", "C_inject"]].median().to_dict()
SUMMARY["C_by_design"] = P.groupby("design")[["C_drop", "C_flip", "C_inject"]].median().to_dict()
SUMMARY["flip_over_drop_median"] = float((R.k_flip / R.k_drop).median())
SUMMARY["inject_over_drop_median"] = float((R.k_inject / R.k_drop).median())
SUMMARY["lin_over_refit_drop_median"] = float((R.k_drop_lin / R.k_drop)[np.isfinite(R.k_drop_lin)].median())

# ------------------------------------------------------------------ same-battle comparison
st = ["arenaST_human"] + ["arenaST_" + j for j in D.JUDGES]
st = [s for s in st if s in metas]
if len(st) > 1:
    import scipy.stats as ss
    from lbstab.prep import prepare
    hum = metas["arenaST_human"]
    th_h = dict(zip(hum["names"], np.array(hum["theta"])[:hum["m"]]))
    jt = pd.read_json(os.path.join(D.DATA, "judges", "train.single-turn.json"))[["id", "winner_model_a", "winner_model_b", "winner_tie"]]
    gt = np.where(jt.winner_model_a == 1, "A", np.where(jt.winner_model_b == 1, "B", "tie"))
    gtmap = dict(zip(jt.id, gt))
    srows = []
    for s in st:
        m = metas[s]
        r = R[R.ds == s]
        names = m["names"]
        th = dict(zip(names, np.array(m["theta"])[:m["m"]]))
        common = [n_ for n_ in names if n_ in th_h]
        tau = ss.kendalltau([th[n_] for n_ in common], [th_h[n_] for n_ in common]).statistic
        if s == "arenaST_human":
            agree = 1.0
        else:
            jj = pd.read_json(os.path.join(D.DATA, "judges", "llm-judges-prob-avg", s.replace("arenaST_", "") + ".jsonl"), lines=True)
            agree = float(np.mean(jj.winner_pred.values == np.array([gtmap[i] for i in jj.id])))
        tb = top_budgets(r, m)
        top10 = r[(r.rank_j == r.rank_i + 1) & (r.rank_i < 10)]
        srows.append(dict(ds=s, tie=m["tie_rate"], agree=agree, tau=tau, top1=tb["top1_names"][0],
                          top1_z=tb["top1_z"], top1_drop=tb["top1_drop"], top1_flip=tb["top1_flip"],
                          top1_inject=tb["top1_inject"], top5_drop=tb["top5_drop"],
                          adj10_z=top10.z.median(), adj10_drop=top10.k_drop.median(),
                          all_z=r.z.median(), all_drop=r.k_drop.median(),
                          C=P[P.ds == s].C_drop.median(), spread=np.std(np.array(m["theta"])[:m["m"]]), n=m["n"]))
    S = pd.DataFrame(srows)
    S.to_csv(os.path.join(RES, "table_same_battles.csv"), index=False)
    with open(os.path.join(TAB, "same_battles.tex"), "w") as f:
        for _, x in S.iterrows():
            f.write(f"{PRETTY[x.ds].replace('Arena-ST ','').strip('()')} & {x.tie:.2f} & {x.agree:.2f} & {x.tau:.2f} & {x.spread:.2f} & "
                    f"{x.top1_z:.2f} & {int(x.top1_drop)} & {int(x.top5_drop)} & {x.adj10_z:.2f} & {x.adj10_drop:.0f} & {x.all_drop:.0f} & {x.C:.2f} \\\\\n")

# ------------------------------------------------------------------ MT-Bench matched
SUMMARY["mtbench"] = {}
for s in ["mtbench_human", "mtbench_gpt4"]:
    if s in metas:
        r = R[R.ds == s]
        SUMMARY["mtbench"][s] = dict(order=[metas[s]["names"][k] for k in metas[s]["order"]],
                                     adj=r[r.rank_j == r.rank_i + 1][["rank_i", "z", "k_drop", "k_flip", "k_inject"]].to_dict("records"))

json.dump(SUMMARY, open(os.path.join(RES, "summary.json"), "w"), indent=1, default=str)
print(T.to_string())
print(json.dumps(SUMMARY["law"], indent=1))
