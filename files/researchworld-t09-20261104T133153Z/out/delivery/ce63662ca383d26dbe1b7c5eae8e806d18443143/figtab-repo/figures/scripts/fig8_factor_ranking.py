"""Fig 8 (claim C3): which factors move the error most? For the regression estimator OLS (z,f) (filled dots) and the correctly
specified regression (open), RMSE (in units of the direct effect $\\tau$=1) at each level of one factor, all other factors held at the sweep's
default. Each row is a separate one-factor sweep from the experiment named in the row label (base scenarios differ between
sweeps, listed in the label), so the rows compare the *size of the range*, not absolute positions. Bars span min-max;
end points are annotated by level. Ordered by max/min of the OLS (z,f) RMSE; identical to results/tables/t11_factor_ranking.csv (asserted)."""
import numpy as np
import matplotlib.pyplot as plt
from common import *


def sweeps():
    """Same sweeps, grids and filters as experiment-repo `factor_ranking.py` (results/tables/t11_factor_ranking.csv); main() checks the ratios against that table."""
    e1, e2, e3, e5 = [load(e) for e in ["e1", "e2", "e3", "e5"]]
    SBM = "sbm:5000,50,20,0.8"
    S = []
    add = lambda name, d, lev, fmt: S.append((name, d, lev, fmt))
    base = e2[(e2.graph == SBM) & (e2.o_kind == "concave")]
    add("spillover shape (e2, SBM, Bernoulli(0.5), $\\gamma$=2)", e2[(e2.graph == SBM) & (e2.design == "bern:0.5")], "o_kind", str)
    add("treatment prob. $p$ (e2, SBM, concave)", base[base.design.isin(["bern:0.5", "bern:0.1"])], "p", lambda v: f"{v:g}")
    d = base[base.design.isin(["bern:0.5", "louv:1.0,0.5", "rand:1.0,0.5"])].copy(); d["dl"] = d.dkind.map({"bern": "Bern", "louv": "graph cl.", "rand": "random cl."})
    add("design (e2, SBM, concave)", d, "dl", str)
    add("graph family (e2, Bernoulli(0.5), concave)", e2[(e2.design == "bern:0.5") & (e2.o_kind == "concave")], "gname", str)
    add("interference strength $\\gamma$ (e1, SBM, linear)", e1[(e1.graph == SBM) & (e1.design == "bern:0.5")], "o_gamma", lambda v: f"{v:g}")
    d = e3[e3.graph.str.startswith("er:") & e3.graph.str.contains(",20$")]
    add("number of units $n$ (e3, ER, $d$=20, linear)", d, "n_nom", lambda v: f"{v:g}")
    d = e3[e3.graph.str.startswith("er:5000,")]
    add("mean degree $d$ (e3, ER, $n$=5000, linear)", d, "d_nom", lambda v: f"{v:g}")
    d = e5[(e5.graph == SBM) & (e5.design == "bern:0.5") & (e5.o_alpha_graph == 1.0)]
    add("noise SD $\\sigma$ (e5, SBM, linear, $\\alpha_{graph}$=1)", d, "o_sigma", lambda v: f"{v:g}")
    return S


def main():
    style()
    rows = []
    for name, d, lev, fmt in sweeps():
        rec = {}
        for est in ["OLS_f", "ORACLE_D"]:
            if est == "OLS_f":
                s = d[d.est_name == "OLS_f"]
            else:  # oracle with the log-degree term where the sweep has it, else the plain oracle
                has = (d.est_name == "ORACLE_D").any()
                s = d[d.est_name == ("ORACLE_D" if has else "ORACLE")]
            s = s.dropna(subset=["rmse"]).sort_values(lev)
            if s.empty or s[lev].nunique() < 2:
                continue
            rec[est] = s
        if "OLS_f" in rec:
            s = rec["OLS_f"]
            rows.append((name, rec, lev, fmt, s.rmse.max() / s.rmse.min()))
    rows.sort(key=lambda r: -r[-1])
    t11 = pd.read_csv(os.path.join(RES, "..", "tables", "t11_factor_ranking.csv"))
    assert np.allclose(sorted(t11.ratio_max_min), sorted(r[-1] for r in rows), rtol=1e-6), "fig8 differs from t11_factor_ranking.csv"
    fig, ax = plt.subplots(figsize=(TEXTW, 0.25 * len(rows) + 0.5))
    for k, (name, rec, lev, fmt, ratio) in enumerate(rows):
        y = len(rows) - 1 - k
        for est, off, filled in [("OLS_f", 0.12, True), ("ORACLE_D", -0.12, False)]:
            if est not in rec:
                continue
            s = rec[est]; v = s.rmse.values
            ax.plot([v.min(), v.max()], [y + off] * 2, color=ECOL[est], lw=1.2)
            ax.plot(v, [y + off] * len(v), "o", ms=3.2, color=ECOL[est], mfc=ECOL[est] if filled else "white", mew=0.8)
            if filled:
                i0, i1 = np.argmin(v), np.argmax(v)
                ax.annotate(fmt(s[lev].values[i0]), (v[i0], y + off), xytext=(-3, 4), textcoords="offset points", fontsize=5.5, ha="right")
                ax.annotate(fmt(s[lev].values[i1]), (v[i1], y + off), xytext=(3, 4), textcoords="offset points", fontsize=5.5, ha="left")
        ax.text(1.005, y + 0.12, f"$\\times${ratio:.1f}", transform=ax.get_yaxis_transform(), fontsize=6.5, va="center")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=6.5)
    ax.set_xscale("log"); ax.set_xticks([0.05, 0.1, 0.2, 0.5, 1, 2, 5]); plainlog(ax, "x"); ax.minorticks_off(); ax.set_xlabel("RMSE (units of direct effect $\\tau=1$)")
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], color=ECOL["OLS_f"], marker="o", ms=3.2, label="OLS $z,f$"),
                       Line2D([], [], color=ECOL["ORACLE_D"], marker="o", mfc="white", ms=3.2, label="correctly specified")], loc="lower right", fontsize=6.5)
    ax.text(1.005, 1.01, "ratio", transform=ax.transAxes, fontsize=6.5, ha="left")
    fig.tight_layout()
    save(fig, "fig8_factor_ranking")


if __name__ == "__main__":
    main()
