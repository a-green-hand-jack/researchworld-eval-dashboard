"""LaTeX tables (paper/tables/*.tex) from results CSVs."""
import os, numpy as np, pandas as pd, json
from ac import *

def fmt(x, d=2):
    return "--" if (x is None or (isinstance(x, float) and np.isnan(x))) else f"{x:.{d}f}"

def cell(b, r, d=2):
    if b is None or (isinstance(b, float) and np.isnan(b)):
        return "--"
    return f"{b:+.{d}f} ({r:.{d}f})"

# ------------------------------------------------------------------ Table: extrapolation (E2 + E2g)
def tab_extrap():
    df = load("E2"); df["gl"] = gkey(df)
    df["shape"] = df.apply(lambda r: f"k={r.mech_k:g}" if r.mech_shape == "pow" else "threshold", axis=1)
    g2 = None
    if os.path.exists(f"{RES}/E2g.csv"):
        g2 = load("E2g"); g2["gl"] = gkey(g2)
        g2["shape"] = g2.apply(lambda r: f"k={r.mech_k:g}" if r.mech_shape == "pow" else "threshold", axis=1)
    ests = [("ols_s", r"\textsc{ols-s}"), ("ols_s_quad", r"+$s^2$"), ("ols_s_cub", r"+$s^2,s^3$"), ("gbm", r"\textsc{gbm}$^\dagger$"), ("hajek", r"H\'ajek")]
    lines = []
    for gl in ["ER", "ego-Facebook", "Stanford3"]:
        for sh in ["k=4", "threshold"]:
            for des in ["bern", "cluster"]:
                row = [gl if (sh == "k=4" and des == "bern") else "", sh if des == "bern" else "", "Bern." if des == "bern" else "cluster"]
                s = df[(df.gl == gl) & (df["shape"] == sh) & (df.design_type == des)]
                for e, _ in ests:
                    if e == "gbm":
                        t = g2[(g2.gl == gl) & (g2["shape"] == sh) & (g2.design_type == des) & (g2.estimator == "gbm")] if g2 is not None else pd.DataFrame()
                    else:
                        t = s[s.estimator == e]
                    if len(t) and e == "hajek":
                        t = t[t.fail < 0.5]
                    row.append(cell(t.bias.mean(), t.rmse.mean()) if len(t) else "--")
                lines.append(" & ".join(row) + r" \\")
            lines.append(r"\addlinespace[1pt]") if False else None
    hdr = " & ".join(["graph", "response", "design"] + [n for _, n in ests]) + r" \\"
    tex = (r"\begin{table}[t]\centering\footnotesize\setlength{\tabcolsep}{3.5pt}" "\n"
           r"\caption{Nonlinear exposure response (E2): bias (RMSE) of the GATE estimate; true GATE $\approx2$. Mean over 6 worlds ($R{=}300$). $^\dagger$ \textsc{gbm}: 3 worlds, $R{=}40$ assignments each. ``--'': H\'ajek undefined in $\ge50\%$ of draws (or not run).}" "\n"
           r"\label{tab:extrap}" "\n" r"\begin{tabular}{lllccccc}\toprule" "\n" + hdr + "\n" + r"\midrule" "\n" + "\n".join(lines) + "\n" r"\bottomrule\end{tabular}\end{table}" "\n")
    open(f"{TAB}/tab_extrap.tex", "w").write(tex)

# ------------------------------------------------------------------ Table: multi-hop
def tab_mh():
    df = load("E3"); df = df[df.tag == "multihop"].copy(); df["gl"] = gkey(df)
    df["fam"] = df.gl + "/" + df.design_type.map({"bern": "Bern.", "cluster": "cluster"})
    ex = pd.read_csv(f"{TAB}/multihop_exact.csv")
    lines = []
    for fam in ["ER/Bern.", "SBM/Bern.", "SBM/cluster", "ego-Facebook/Bern.", "ego-Facebook/cluster", "Stanford3/Bern.", "Stanford3/cluster"]:
        s = df[(df.fam == fam) & (df.mech_lam == 0.6)]
        row = [fam.replace("ego-Facebook", "ego-FB"), fmt(s[s.estimator == "ols_s"].truth.mean())]
        for e in ["dm", "ols_s", "ols_s2"]:
            t = s[s.estimator == e]
            row.append(cell(t.bias.mean(), t.rmse.mean()))
        if fam.endswith("Bern.") and fam.split("/")[0] in ("ER", "ego-Facebook", "Stanford3"):
            e_ = ex[(ex.graph == fam.split("/")[0]) & (ex.lam == 0.6)].iloc[0]
            row += [fmt(e_.exact, 3), fmt(e_.tree, 3)]
        else:
            row += ["--", fmt(-0.6 ** 2 / 0.4, 3) if fam.startswith("SBM/Bern") else "--"]
        lines.append(" & ".join(row) + r" \\")
    tex = (r"\begin{table}[t]\centering\footnotesize\setlength{\tabcolsep}{3.5pt}" "\n"
           r"\caption{Multi-hop spillover, $\lambda=0.6$ (E3): bias (RMSE) of DiM, one-hop regression and regression with two-step exposure; last two columns: closed-form bias of the one-hop regression under Bernoulli designs (exact walk-statistics formula, tree-like approximation). Mean over 6 worlds.}" "\n"
           r"\label{tab:mh}" "\n" r"\begin{tabular}{llccccc}\toprule" "\n"
           r"graph/design & GATE & DiM & \textsc{ols-s} & \textsc{ols-s2} & $B$ exact & $B$ tree \\" "\n" r"\midrule" "\n" + "\n".join(lines) + "\n" r"\bottomrule\end{tabular}\end{table}" "\n")
    open(f"{TAB}/tab_mh.tex", "w").write(tex)

# ------------------------------------------------------------------ Table: heterogeneity
def tab_het():
    import sys; sys.path.insert(0, "/work/code")
    from sim import build_graph, World
    df = load("E3"); df = df[df.tag == "gamhet"].copy(); df["gl"] = gkey(df)
    if "wls_s" not in set(df.estimator):
        return
    df["gh"] = df.mech_gam_het
    lines = []
    cols = [("ols_s", r"\textsc{ols-s}"), ("ols_s_cnt", r"$+c$"), ("ols_s_deg", r"\textsc{s-deg}"), ("wls_s", r"\textsc{wls-s}"), ("strat_s", r"\textsc{strat-s}")]
    for gl, gm in [("Stanford3", None), ("ego-Facebook", None)]:
        for gh in ["none", "inv", "pos"]:
            for des in ["bern", "cluster"]:
                s = df[(df.gl == gl) & (df.gh == gh) & (df.design_type == des)]
                if gm is not None:
                    s = s[s.graph_m == gm]
                if len(s) == 0:
                    continue
                row = [gl if (gh == "none" and des == "bern") else "", gh if des == "bern" else "", "Bern." if des == "bern" else "cluster"]
                # Prop. 4 prediction (Bernoulli only), computed on the actual worlds
                if des == "bern":
                    if gl == "BA":
                        spec = dict(name="ba", n=4000, m=5)
                    else:
                        spec = dict(name="stanford3" if gl == "Stanford3" else "egofb")
                    pb = []
                    for wi in range(6):
                        gs = 100 + wi if gl == "BA" else 0
                        A = build_graph(spec, gs)
                        w = World(A, dict(kind="frac", shape="pow", k=1.0, gamma=1.0, gam_het=gh), 1000 + wi)
                        pi = (1 / w.deg) / np.sum(1 / w.deg)
                        pb.append(np.sum(pi * w.gi) - np.mean(w.gi))
                    row.append(f"{np.mean(pb):+.2f}")
                else:
                    row.append("--")
                for e, _ in cols:
                    t = s[s.estimator == e]
                    row.append(cell(t.bias.mean(), t.rmse.mean()) if len(t) else "--")
                lines.append(" & ".join(row) + r" \\")
        lines.append(r"\midrule")
    lines = lines[:-1]
    hdr = " & ".join(["graph", r"$\gamma_i$ het.", "design", r"$B$ (Prop.~\ref{prop:wt})"] + [n for _, n in cols]) + r" \\"
    tex = (r"\begin{table}[t]\centering\footnotesize\setlength{\tabcolsep}{3pt}" "\n"
           r"\caption{Degree-heterogeneous spillover (E3): bias (RMSE); true GATE $\approx2$. ``inv'': low-degree units are more susceptible, ``pos'': high-degree units. $B$: bias predicted by Prop.~\ref{prop:wt} for \textsc{ols-s}. $+c$: model with $s$ and the neighbour count; \textsc{s-deg}: $s$ and $s\times$log-degree; \textsc{wls-s}: weights $1/\mathrm{Var}(s_i)$; \textsc{strat-s}: separate fits in 5 degree strata (the last two designed after the pilot, see text). Mean over 6 worlds.}" "\n"
           r"\label{tab:het}" "\n" r"\begin{tabular}{lllccccc c}\toprule" "\n" + hdr + "\n" r"\midrule" "\n" + "\n".join(lines) + "\n" r"\bottomrule\end{tabular}\end{table}" "\n")
    # one column too many in tabular spec fix
    tex = tex.replace(r"\begin{tabular}{lllccccc c}", r"\begin{tabular}{lllcccccc}")
    open(f"{TAB}/tab_het.tex", "w").write(tex)

def tab_cross():
    ct = pd.read_csv(f"{TAB}/crossover.csv")
    lines = [f"{int(r.d)} & {int(r.n)} & {r.gstar:.3f} & {r.pred_closed:.3f} & {r.dm0:.3f} & {r.ols0:.3f} \\\\" for r in ct.itertuples()]
    h = df = load("E1"); h = h[(h.estimator == "hajek") & (h.tag == "er_d")]
    fr = h.groupby("graph_d").fail.mean()
    tex = (r"\begin{table}[t]\centering\footnotesize" "\n"
           r"\caption{Crossover spillover strength $\gamma^\ast$ above which the one-hop regression has lower RMSE than DiM (E4; ER graphs, Bernoulli; $\beta\approx1$), versus $\hat\kappa\sqrt{L/n}$; RMSE of DiM and regression at $\gamma=0$. H\'ajek (E1, $n=4000$) is undefined in a fraction " + ", ".join(f"{v:.2f}" for v in fr.values) + r" of draws for $d=" + ",".join(str(int(k)) for k in fr.index) + r"$ respectively.}" "\n"
           r"\label{tab:cross}\begin{tabular}{rrrrrr}\toprule" "\n" r"$d$ & $n$ & $\gamma^\ast$ (obs.) & $\hat\kappa\sqrt{L/n}$ & DiM RMSE & reg. RMSE \\" "\n" r"\midrule" "\n" + "\n".join(lines) + "\n" r"\bottomrule\end{tabular}\end{table}" "\n")
    open(f"{TAB}/tab_cross.tex", "w").write(tex)

if __name__ == "__main__":
    for f in (tab_extrap, tab_mh, tab_het, tab_cross):
        try:
            f(); print("ok", f.__name__)
        except Exception as e:
            import traceback; traceback.print_exc(); print("FAILED", f.__name__, e)

def tab_app():
    """appendix tables: leverage ratio, noise scale, cluster-quality"""
    df = load("E1"); df["gl"] = gkey(df)
    o = df[(df.estimator == "ols_s") & (df.tag != "er_siga")].copy()
    o["fam"] = o.gl + "/" + o.design_type.map({"bern": "Bern.", "cluster": "cluster"})
    o["levratio"] = o.lev / o.lev_theory
    kappa = json.load(open(f"{TAB}/headline_numbers.json"))["kappa"]
    o["rr"] = o.rmse / (kappa * np.sqrt(o.lev_theory / o.n))
    t = o.groupby("fam").agg(runs=("rmse", "size"), lev_med=("levratio", "median"), lev_min=("levratio", "min"), lev_max=("levratio", "max"),
                             r_med=("rr", "median"), r_min=("rr", "min"), r_max=("rr", "max")).reset_index()
    lines = [f"{r.fam} & {r.runs} & {r.lev_med:.2f} [{r.lev_min:.2f}, {r.lev_max:.2f}] & {r.r_med:.2f} [{r.r_min:.2f}, {r.r_max:.2f}] \\\\" for r in t.itertuples()]
    tex = (r"\begin{table}[h]\centering\footnotesize" "\n"
           r"\caption{Closed-form leverage vs simulation (E1, \textsc{ols-s}). Runs are (setting, world) pairs. Left: simulated mean leverage over $R$ assignments divided by $L$ of Prop.~\ref{prop:lev}; right: observed RMSE divided by $\hat\kappa\sqrt{L/n}$ (median [min, max]).}" "\n"
           r"\label{tab:lev}\begin{tabular}{lrcc}\toprule" "\n" r"family/design & runs & $\bar L_{\rm sim}/L$ & RMSE / predicted \\" "\n" r"\midrule" "\n" + "\n".join(lines) + "\n" r"\bottomrule\end{tabular}\end{table}" "\n")
    open(f"{TAB}/tab_lev.tex", "w").write(tex)
    # sigma_a
    sg = df[(df.estimator == "ols_s") & (df.tag == "er_siga")]
    g = agg_worlds(sg, ["mech_sig_a"])
    lines = [f"{r.mech_sig_a:.2f} & {r.rmse:.3f} & {r.bias:+.3f} \\\\" for r in g.itertuples()]
    tex = (r"\begin{table}[h]\centering\footnotesize" "\n"
           r"\caption{Dependence on the baseline scale $\sigma_a$ (E1; ER, $n=4000$, $d=16$, Bernoulli; effect heterogeneity fixed at $0.5$).}" "\n"
           r"\label{tab:siga}\begin{tabular}{rrr}\toprule" "\n" r"$\sigma_a$ & RMSE & bias \\" "\n" r"\midrule" "\n" + "\n".join(lines) + "\n" r"\bottomrule\end{tabular}\end{table}" "\n")
    open(f"{TAB}/tab_siga.tex", "w").write(tex)
    # cluster quality (E5, K sweep)
    e5 = load("E5"); e5["gl"] = gkey(e5)
    q = e5[(e5.tag == "K_lin") & (e5.estimator == "ols_s")]
    g = agg_worlds(q, ["gl", "design_K"]).sort_values(["gl", "n_clusters"])
    lines = [f"{r.gl} & {r.n_clusters:.0f} & {r.cut_frac:.2f} & {r.lev:.1f} & {r.lev_theory:.1f} & {r.rmse:.3f} \\\\" for r in g.itertuples()]
    tex = (r"\begin{table}[h]\centering\footnotesize" "\n"
           r"\caption{Clustering quality and error (E5, linear response, \textsc{ols-s}, $p=\frac12$): number of Louvain clusters, fraction of edges cut, simulated mean leverage, closed-form leverage, RMSE (means over 6 worlds).}" "\n"
           r"\label{tab:clu}\begin{tabular}{lrrrrr}\toprule" "\n" r"graph & clusters & cut & $\bar L_{\rm sim}$ & $L$ & RMSE \\" "\n" r"\midrule" "\n" + "\n".join(lines) + "\n" r"\bottomrule\end{tabular}\end{table}" "\n")
    open(f"{TAB}/tab_clu.tex", "w").write(tex)

if __name__ == "__main__":
    tab_app(); print("ok tab_app")
