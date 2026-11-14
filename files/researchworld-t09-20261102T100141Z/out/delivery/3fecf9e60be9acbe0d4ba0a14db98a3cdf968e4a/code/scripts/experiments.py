"""Experiment grids. Each experiment = list of cell specs (see netgate.sim.run_cell)."""
import copy, itertools

BASE = dict(
    graph=dict(kind="sbm", n=3000, d=20, mu=0.1),
    outcome=dict(kind="lin_frac", tau=1.0, gamma=1.0, sigma_a=1.0, sigma_c=1.0, rho_deg=0.5, sigma_e=1.0),
    design=dict(kind="bernoulli", p=0.5),
    ests=["dm", "ols_f", "ols_cnt", "ols_f_adj"],
    G=8, R=250, se=True,
)
LIN = ["dm", "hajek", "ols_f", "ols_cnt", "ols_cnt_adj", "ols_f_adj", "ols_f_deg", "ols_f2", "ols_poly"]


def mk(tag, graph=None, outcome=None, design=None, **kw):
    s = copy.deepcopy(BASE)
    s["graph"].update(graph or {}); s["outcome"].update(outcome or {}); s["design"].update(design or {})
    s.update(kw); s["tag"] = tag
    return s


def exp_E1_size():       # error vs n  (correct linear spec); estimator zoo
    return [mk(f"n={n}", graph=dict(n=n), ests=LIN) for n in (500, 1000, 2000, 4000, 8000)]


def exp_E2_degree():     # error vs mean degree, two graph families
    out = []
    for kind in ("sbm", "er"):
        for d in (5, 10, 20, 40, 80, 160):
            out.append(mk(f"{kind}_d={d}", graph=dict(kind=kind, d=d, n=4000), ests=LIN))
    return out


def exp_E3_gamma():      # interference strength
    return [mk(f"gamma={g}", outcome=dict(gamma=g), ests=LIN) for g in (0, 0.25, 0.5, 1, 2, 4)]


def exp_E4_curv():       # nonlinearity x degree x p
    out = []
    shapes = [("pow", dict(q=0.5)), ("pow", dict(q=1.0)), ("pow", dict(q=2.0)), ("pow", dict(q=4.0)),
              ("thresh", dict(steep=10.0, thr=0.5)), ("thresh", dict(steep=10.0, thr=0.9))]
    for (k, kw), d, p in itertools.product(shapes, (10, 40, 160), (0.1, 0.3, 0.5, 0.7, 0.9)):
        tag = f"{k}{'_'.join(f'{a}{b}' for a, b in kw.items())}_d{d}_p{p}"
        out.append(mk(tag, graph=dict(d=d, n=3000), outcome=dict(kind=k, **kw), design=dict(p=p),
                      ests=["dm", "ols_f", "ols_poly", "ols_poly3", "ols_f_adj", "hajek_q0.75"], G=5, R=200, pop=True))
    return out


def exp_E5_graphs():     # graph families
    gs = [dict(kind="er"), dict(kind="ba"), dict(kind="ws", beta=0.1), dict(kind="ws", beta=0.5),
          dict(kind="sbm", mu=0.02), dict(kind="sbm", mu=0.1), dict(kind="sbm", mu=0.4), dict(kind="geo")]
    out = [mk(f"{g['kind']}_{g.get('beta', g.get('mu', ''))}", graph=dict(g, n=4000, d=20), ests=LIN) for g in gs]
    out.append(mk("fb_ego", graph=dict(kind="fb_ego"), ests=LIN, G=1, R=2000))
    out.append(mk("fb_stanford", graph=dict(kind="fb_stanford"), ests=LIN, G=1, R=2000))
    return out


def exp_E6_spec():       # kinds of interference vs feature sets (misspecification)
    ests = ["dm", "ols_f", "ols_cnt", "ols_cnt_adj", "ols_f_both", "ols_f2", "ols_f_adj", "ols_f_deg", "ols_poly"]
    out = []
    for g in (dict(kind="sbm", d=20), dict(kind="ba", d=20), dict(kind="er", d=60)):
        for tag, oc in [("lin_frac", dict(kind="lin_frac")), ("lin_count", dict(kind="lin_count")),
                        ("lin_2hop", dict(kind="lin_2hop", gamma=0.5, gamma2=0.5)),
                        ("het", dict(kind="lin_frac", het=0.5)), ("het_big", dict(kind="lin_frac", het=1.0))]:
            out.append(mk(f"{g['kind']}_d{g['d']}_{tag}", graph=dict(g, n=3000), outcome=oc, ests=ests))
    return out


def exp_E7_model():      # model class under nonlinear interference
    out = []
    for shape in (dict(kind="lin_frac"), dict(kind="pow", q=2.0), dict(kind="thresh", steep=10.0, thr=0.5)):
        for d in (10, 40):
            for p in (0.5,):
                out.append(mk(f"{shape['kind']}{shape.get('q', '')}_d{d}", graph=dict(n=3000, d=d), outcome=shape,
                              design=dict(p=p), ests=["ols_f", "ols_poly", "ols_poly3", "ridge_rich", "gbm"],
                              G=4, R=80, se=False))
    return out


def exp_E8_design():     # Bernoulli vs cluster randomisation (resolution) x nonlinearity
    out = []
    for shape in (dict(kind="lin_frac"), dict(kind="pow", q=2.0), dict(kind="thresh", steep=10.0, thr=0.5)):
        for dg in (dict(kind="bernoulli"), dict(kind="cluster", res=0.3), dict(kind="cluster", res=1.0),
                   dict(kind="cluster", res=3.0)):
            for gr in (dict(kind="sbm", mu=0.05), dict(kind="sbm", mu=0.3)):
                tag = f"{shape['kind']}{shape.get('q', '')}_{dg['kind']}{dg.get('res', '')}_mu{gr['mu']}"
                out.append(mk(tag, graph=dict(gr, n=4000, d=20), outcome=shape, design=dict(dg, p=0.5),
                              ests=["dm", "hajek", "ols_f", "ols_poly", "ols_f_adj"], G=6, R=250))
    return out


def exp_E9_noise():      # noise levels
    out = []
    for se_, sc in itertools.product((0.25, 1, 4), (0, 1, 3)):
        out.append(mk(f"sigE{se_}_sigC{sc}", outcome=dict(sigma_e=se_, sigma_c=sc), ests=LIN))
    return out


def exp_E10_coverage():  # CI calibration, naive vs cluster-robust
    out = []
    for gr in (dict(kind="sbm", mu=0.05), dict(kind="sbm", mu=0.3), dict(kind="er"), dict(kind="ba")):
        for n in (1000, 4000):
            for sc in (True, False):
                out.append(mk(f"{gr['kind']}{gr.get('mu', '')}_n{n}_{'cl' if sc else 'hc'}", graph=dict(gr, n=n, d=20),
                              ests=["ols_f", "ols_f_adj"], se_cluster=sc, G=10, R=300))
    return out


# ---------------- pre-declared main grid (config fixed before looking at estimator results) ----------------
MECH = {"M1": dict(kind="lin_frac"), "M3": dict(kind="sat", steep=3.0), "M4": dict(kind="lin_2hop", gamma=0.5, gamma2=0.5),
        "M5": dict(kind="lin_frac", het=0.5)}
GRAPHS = {"er": dict(kind="er", n=2000, d=10), "sbm": dict(kind="sbm", n=2000, d=10, k=20, mu=0.1),
          "ba": dict(kind="ba", n=2000, d=10), "ws": dict(kind="ws", n=2000, d=10, beta=0.1),
          "fb_ego": dict(kind="fb_ego"), "fb_stanford": dict(kind="fb_stanford")}
DESIGNS = {"bern0.5": dict(kind="bernoulli", p=0.5), "bern0.1": dict(kind="bernoulli", p=0.1),
           "cluster0.5": dict(kind="cluster", p=0.5)}


def _main(ests, tag, G, R_syn, R_real, legacy_k=False, **kw):
    """legacy_k: MAIN and E0_valid were run when the base graph spec carried an inert `k` (ignored for non-SBM graphs); it is part of the
    cell id (hence of the random streams), so it is kept for those two to regenerate the delivered numbers exactly."""
    out = []
    for (gn, g), (mn, m), (dn, d) in itertools.product(GRAPHS.items(), MECH.items(), DESIGNS.items()):
        real = gn.startswith("fb_")
        d = dict(d)
        if d["kind"] == "cluster":
            d["res"] = 10.0 if real else 3.0
        if legacy_k:
            g = dict(g, k=g.get("k", 30), mu=0.1)
        out.append(mk(f"{gn}|{mn}|{dn}", graph=g, outcome=dict(m, tau=1.0, gamma=m.get("gamma", 1.0)), design=d, ests=ests,
                      G=1 if real else G, R=R_real if real else R_syn, **kw))
    return out


def exp_MAIN():          # 6 graphs x 4 mechanisms x 3 designs = 72 cells; OLS family + baselines + approximation error
    return _main(["dm", "hajek", "hajek_q0.75", "ols_f", "ols_f_deg", "ols_f2", "ols_poly", "ols_f_adj"], "main", 5, 100, 500, legacy_k=True, pop=True, se=True)


def exp_MAIN_s2():       # robustness: synthetic MAIN cells under another base seed (SEEDS below); current spec, no legacy key
    return [c for c in _main(["dm", "hajek", "hajek_q0.75", "ols_f", "ols_f_deg", "ols_f2", "ols_poly", "ols_f_adj"], "main", 5, 100, 500,
                             pop=True, se=True) if not c["graph"]["kind"].startswith("fb_")]


def exp_MAIN_realdraws():   # review finding D: real-graph MAIN cells with 8 independent baseline (sigma_a, sigma_c) draws x 60 assignments
    out = []
    for c in _main(["dm", "hajek", "hajek_q0.75", "ols_f", "ols_f_deg", "ols_f2", "ols_poly", "ols_f_adj"], "main", 1, 100, 60, pop=True, se=True):
        if c["graph"]["kind"].startswith("fb_"):
            c["G"] = 8
            out.append(c)
    return out


SEEDS = {"MAIN_s2": 777}   # base seed per experiment (default 20261102)


def exp_MAINML():        # same 72 cells: flexible learners (ridge on rich features, gradient boosting) + OLS reference
    return _main(["ols_f", "ridge_rich", "gbm"], "mainml", 5, 100, 200, pop=True, se=False)


def exp_E0_valid():      # validity: no-interference + clean baseline => all unbiased; Chin-style reference setting
    clean = dict(rho_deg=0.0, sigma_c=0.0)
    out = [mk("valid_gamma0", graph=dict(kind="er", n=2000, d=10, k=30), outcome=dict(clean, gamma=0.0),
              ests=["dm", "hajek_q0.75", "ols_f", "ols_cnt", "ols_f_adj", "ols_poly"], G=4, R=500),
           mk("valid_M1_clean", graph=dict(kind="er", n=2000, d=10, k=30), outcome=dict(clean),
              ests=["dm", "hajek_q0.75", "ols_f", "ols_cnt", "ols_f_adj", "ols_poly"], G=4, R=500)]
    for gn in ("fb_stanford", "fb_ego"):
        out.append(mk(f"chin_{gn}", graph=dict(kind=gn, k=30), outcome=dict(clean), design=dict(p=0.5),
                      ests=["dm", "hajek_q0.75", "ols_f", "ols_f_adj", "ols_cnt_adj"], G=1, R=1000, se=True))
    return out


def exp_E11_grapherr():  # H5: misspecified feature graph
    out = []
    for oc in (dict(kind="lin_frac"), dict(kind="lin_frac", gamma=0.25)):
        for gr in (dict(kind="sbm", n=2000, d=10, k=20, mu=0.1), dict(kind="fb_ego")):
            for r in (0.0, 0.05, 0.1, 0.2, 0.3, 0.5):
                out.append(mk(f"err{r}|{gr['kind']}|gamma{oc.get('gamma', 1.0)}", graph=gr, outcome=oc, graph_err=r,
                              ests=["dm", "ols_f", "ols_f_adj", "ols_poly"], G=8 if gr["kind"] == "sbm" else 12,
                              R=50 if gr["kind"] == "sbm" else 40, pop=True))   # each graph draw = new perturbation + new baseline
    return out


EXPS = {k[4:]: v for k, v in list(globals().items()) if k.startswith("exp_")}
