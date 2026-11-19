"""R4: does the breadth fraction k/m of median-type rules (median, plurality, Copeland) relative to mean-type rules (mean, z-mean) rise with m?
usage: r4.py RAWDIR OUTDIR     reads RAWDIR/e2_helm_s*.csv and e2_helmbig_s*.csv (HELM random subsets, same models) and RAWDIR/e2_ollb_s*.csv (OLLB m=6 bundled vs m=39 free).
Statistic (HELM): slope of the ratio  mean_k_frac(median-type) / mean_k_frac(mean-type)  against ln m, computed per (m, draw) over that draw's targets where no rule
is already first; the draws are resampled within each m (cluster = subset draw; the rules are paired inside a draw). 'diff' is the same slope for the difference.
(OLLB): ratio at m=39 (free, sub-task level) minus ratio at m=6 (bundled, benchmark level), cluster bootstrap over target families.
Only (target, draw) cells that are feasible for every rule at the budget enter; the number of dropped cells is reported."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
RAW, OUT = sys.argv[1], sys.argv[2]
NB = int(os.environ.get("NBOOT", 2000)); rng = np.random.default_rng(20260103)
MEAN, MED = ["mean", "zmean"], ["median", "plurality", "copeland"]


def helm(draws, variant, kcol="k_breadth", feas="feas_breadth"):
    """variant 'feasible': keep (draw, target) cells feasible for every rule at the budget; 'inf1': an infeasible plan counts as breadth fraction 1 (a lower bound)."""
    rows = []
    for b, d in draws.groupby("b"):
        d = d.copy(); d["kf"] = np.where(d[feas], d[kcol] / d.m, 1.0)
        ok = d.groupby(["m_sub", "draw", "target"]).apply(lambda g: bool((g.gap0 > 0).all() and (g[feas].all() or variant == "inf1")), include_groups=False)
        dropped = int((~ok).sum()); total = len(ok)
        d = d.set_index(["m_sub", "draw", "target"]).loc[ok[ok].index].reset_index()
        cell = d.pivot_table(index=["m_sub", "draw"], columns="rule", values="kf", aggfunc="mean")
        for name, num in [("median-type", MED)] + [(r, [r]) for r in MED]:
            for stat in ("ratio", "diff"):
                v = cell[num].mean(axis=1) / cell[MEAN].mean(axis=1) if stat == "ratio" else cell[num].mean(axis=1) - cell[MEAN].mean(axis=1)
                v = v.replace([np.inf, -np.inf], np.nan).dropna().rename("v").reset_index(); v["lm"] = np.log(v.m_sub)
                slope = lambda x: np.polyfit(x.lm, x.v, 1)[0]
                s0 = slope(v); groups = [x.index.values for _, x in v.groupby("m_sub")]
                bs = []
                for _ in range(NB):
                    idx = np.concatenate([rng.choice(g, len(g)) for g in groups]); bs.append(slope(v.loc[idx]))
                rows.append(dict(regime="helm_subset", variant=variant, rule_pair=f"{name} / {'+'.join(MEAN)}", statistic=f"slope_{stat}_vs_ln_m", B_sigma=b, slope=s0,
                                 ci_lo=np.percentile(bs, 2.5), ci_hi=np.percentile(bs, 97.5), n_draws=len(v), n_clusters=len(v), n_cells_dropped=dropped, n_cells=total,
                                 by_m=";".join(f"{int(m)}:{x.v.mean():.3f}" for m, x in v.groupby("m_sub"))))
    return pd.DataFrame(rows)


def ollb(d, variant, kcol="k_breadth", feas="feas_breadth"):
    from lbprice.boards import load_ollb, ollb_family
    fam = dict(zip(*(lambda b: (b["names"], ollb_family(b["meta"])[1]))(load_ollb("m39"))))
    rows = []
    for b, dd in d.groupby("b"):
        dd = dd.copy(); dd["kf"] = np.where(dd[feas], dd[kcol] / dd.m, 1.0); dd["family"] = dd.model.map(fam)
        for mean_name, mean_rules in (("meanh+zmean", {"m39": ["meanh", "zmean"], "m6raw": ["mean", "zmean"]}), ("mean+zmean (flat)", {"m39": ["mean", "zmean"], "m6raw": ["mean", "zmean"]})):
            piv = {bd: dd[dd.board == bd].pivot_table(index=["model", "family"], columns="rule", values="kf", aggfunc="first") for bd in ("m6raw", "m39")}
            feasd = {bd: dd[dd.board == bd].pivot_table(index=["model", "family"], columns="rule", values=feas, aggfunc="first") for bd in ("m6raw", "m39")}
            gapd = {bd: dd[dd.board == bd].pivot_table(index=["model", "family"], columns="rule", values="gap0", aggfunc="first") for bd in ("m6raw", "m39")}
            idx = piv["m6raw"].index.intersection(piv["m39"].index)
            allr = sorted(set(MED) | set(mean_rules["m39"]))
            keep = [i for i in idx if (variant == "inf1" or (all(feasd["m39"].loc[i, r] for r in allr if r in feasd["m39"]) and all(feasd["m6raw"].loc[i, r] for r in MED + mean_rules["m6raw"])))
                    and all(gapd["m39"].loc[i, r] > 0 for r in allr) and all(gapd["m6raw"].loc[i, r] > 0 for r in MED + mean_rules["m6raw"])]
            for name, num in [("median-type", MED)] + [(r, [r]) for r in MED]:
                comp = {}
                for bd in ("m6raw", "m39"):
                    P = piv[bd].loc[keep]; comp[bd] = (P[num].mean(axis=1), P[mean_rules[bd]].mean(axis=1))
                for stat in ("ratio", "diff"):
                    f = (lambda a, c: a / c) if stat == "ratio" else (lambda a, c: a - c)
                    t = pd.DataFrame(dict(v39=f(*comp["m39"]), v6=f(*comp["m6raw"]))).replace([np.inf, -np.inf], np.nan).dropna()
                    t["delta"] = t.v39 - t.v6; t["family"] = [i[1] for i in t.index]
                    from stats import cluster_mean_ci
                    est = cluster_mean_ci(t.delta, [t.family], nboot=NB, seed=5)
                    rows.append(dict(regime="ollb_free_vs_bundled", variant=variant, rule_pair=f"{name} / {mean_name}", statistic=f"{stat}_m39_minus_m6", B_sigma=b, slope=est[0], ci_lo=est[1], ci_hi=est[2],
                                     n_draws=len(t), n_clusters=est[3], n_cells_dropped=len(idx) - len(keep), n_cells=len(idx), by_m=f"6:{t.v6.mean():.3f};39:{t.v39.mean():.3f}"))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); parts = []
    h = glob.glob(f"{RAW}/e2_helm_s*.csv") + glob.glob(f"{RAW}/e2_helmbig_s*.csv")
    if h:
        hd = pd.concat([pd.read_csv(f) for f in sorted(h)]).drop_duplicates(["m_sub", "draw", "target", "rule", "b"])  # m=25 draw repeated in the big-m shards
        parts += [helm(hd, v) for v in ("feasible", "inf1")]
    o = glob.glob(f"{RAW}/e2_ollb_s*.csv")
    if o: parts += [ollb(pd.concat([pd.read_csv(f) for f in sorted(o)]), v) for v in ("feasible", "inf1")]
    r = pd.concat(parts); r.to_csv(f"{OUT}/m_effect_fit.csv", index=False)
    print(r[r.rule_pair.str.startswith("median-type")].round(3).to_string())
