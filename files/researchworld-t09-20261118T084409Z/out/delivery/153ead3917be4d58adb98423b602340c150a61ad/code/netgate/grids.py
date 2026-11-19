"""Experiment grids (one function per experiment). A cell is the dict consumed by runner.run_cell."""
import itertools

R_DEFAULT = 300


def _cell(graph, out, design, **kw):
    return dict(graph=graph, out=out, design=design, **kw)


def e1_iid_slice(R=400):
    """C1: correct model (REG-L on a linear response, REG-O), sigma_idio>0, Bernoulli. RMSE vs n, d, p."""
    cells = []
    for n, d, p, sig in itertools.product([500, 1000, 2000, 4000, 8000], [5, 10, 20, 40, 80], [0.1, 0.3, 0.5], [0.5, 1.0]):
        cells.append(_cell(dict(kind="er", n=n, d=d), dict(kappa=0.0, gamma=1.0, sigma=sig), dict(kind="bern", p=p),
                           regs=["REG-L", "REG-O"], n_rep=R, theory_M=20, sandwich=True))
    return cells


def e1b_graphs(R=300):
    """C1 on other graph families (linear response, sigma>0): does L predict the sd?"""
    cells = []
    for kind, d, p in itertools.product(["er", "sbm", "ba", "ws"], [5, 10, 20, 40], [0.2, 0.5]):
        cells.append(_cell(dict(kind=kind, n=2000, d=d), dict(kappa=0.0, gamma=1.0, sigma=1.0), dict(kind="bern", p=p),
                           regs=["REG-L", "REG-Lc", "REG-O"], n_rep=R, theory_M=20, sandwich=True))
    return cells


def e2_bias(R=200):
    """C2/C1b: misspecified response. kappa x shape x p x d x noise, ER n=2000. exact projection bias vs measured."""
    cells = []
    for kappa, shape, p, d, sig in itertools.product([0.0, 0.25, 0.5, 1.0], ["convex", "concave", "thresh"],
                                                     [0.1, 0.25, 0.5, 0.75], [5, 10, 20, 50], [0.0, 0.5]):
        if kappa == 0.0 and shape != "convex":
            continue
        cells.append(_cell(dict(kind="er", n=2000, d=d), dict(kappa=kappa, shape=shape, gamma=1.0, sigma=sig,
                           sigma_alpha=0.5 if sig == 0 else 0.0),
                           dict(kind="bern", p=p), regs=["REG-L", "REG-Q", "REG-G", "REG-O"], n_rep=R, theory_M=30, sandwich=True))
    return cells


def e2b_plateau(R=200):
    """C2: bias does not shrink with n (kappa=1 thresh and convex, p=0.25)."""
    cells = []
    for n, shape, sig in itertools.product([250, 500, 1000, 2000, 4000, 8000], ["convex", "thresh"], [0.0, 0.5]):
        cells.append(_cell(dict(kind="er", n=n, d=20), dict(kappa=1.0, shape=shape, gamma=1.0, sigma=sig,
                           sigma_alpha=0.5 if sig == 0 else 0.0),
                           dict(kind="bern", p=0.25), regs=["REG-L", "REG-Q", "REG-O"], n_rep=R, theory_M=30))
    return cells


def e3_crossover(R=300):
    """C3: regression vs HT/Hajek vs DM as a function of d. HT variance exact (design-based)."""
    cells = []
    for d, shape, kappa, p, sig in itertools.product([2, 3, 4, 5, 7, 10, 15, 20, 30, 50], ["convex", "thresh"], [0.0, 0.5, 1.0],
                                                      [0.2, 0.5], [0.5]):
        if kappa == 0.0 and shape == "thresh":
            continue
        cells.append(_cell(dict(kind="er", n=2000, d=d), dict(kappa=kappa, shape=shape, gamma=1.0, sigma=sig),
                           dict(kind="bern", p=p), regs=["REG-L", "REG-Q", "REG-O"], ht=True, ht_deltas=[0.25, 0.5],
                           n_rep=R, theory_M=20))
    return cells


def e4_collapse(R=200):
    """C4 pilot/main: error vs Z across graph families (synthetic at several d; real graphs thinned to vary d)."""
    cells = []
    graphs = [dict(kind=k, n=2000, d=d) for k in ["er", "sbm", "ba", "ws"] for d in [5, 10, 20, 40, 80]]
    graphs += [dict(kind="stanford3", q=q) for q in [0.05, 0.1, 0.2, 0.4, 1.0]]
    graphs += [dict(kind="egofb", q=q) for q in [0.1, 0.25, 0.5, 1.0]]
    outs = [dict(kappa=0.0, gamma=1.0, sigma=1.0),
            dict(kappa=0.5, shape="thresh", gamma=1.0, sigma=0.5),
            dict(kappa=1.0, shape="concave", gamma=1.0, sigma=0.0, sigma_alpha=0.5)]
    for g, o, p in itertools.product(graphs, outs, [0.1, 0.25, 0.5]):
        cells.append(_cell(g, o, dict(kind="bern", p=p), regs=["REG-L", "REG-Lc", "REG-Q", "REG-G", "REG-O"], ht=True,
                           ht_deltas=[0.25], n_rep=R, theory_M=10, sandwich=True))
    return cells


def e7_diagnostic(R=120):
    """H6/H7 evaluation grid (pre-registered in PREREG.md). Fresh seeds via the grid name in the cell config."""
    cells = []
    outs = [dict(kappa=0.0, gamma=1.0, sigma=1.0),
            dict(kappa=1.0, shape="convex", gamma=1.0, sigma=0.5),
            dict(kappa=1.0, shape="concave", gamma=1.0, sigma=0.0, sigma_alpha=0.5),
            dict(kappa=1.0, shape="thresh", gamma=1.0, sigma=0.5),
            dict(kappa=0.5, shape="convex", gamma=1.0, sigma=0.5, w2=0.5),
            dict(kind="count", gamma=1.0, sigma=0.5)]
    for kind, d, p, o in itertools.product(["er", "sbm", "ba", "ws"], [5, 10, 20, 40, 80], [0.1, 0.25, 0.5, 0.75], outs):
        cells.append(_cell(dict(kind=kind, n=2000, d=d), o, dict(kind="bern", p=p), regs=["REG-L", "REG-Q", "REG-G", "REG-O"],
                           n_rep=R, sandwich=True, diag=True, theory_M=20, tag="e7"))
    return cells


def e12_transport(R=100):
    """D4 degree transport (PREREG addendum, fixed before this grid was generated): heterogeneous graphs and an ER control, responses without
    and with degree dependence; D1-D3 and the baselines are computed on the same replicates."""
    cells = []
    graphs = [dict(kind="ba", n=2000, d=d) for d in [5, 10, 20]] + [dict(kind="stanford3", q=q) for q in [0.05, 0.1, 0.2]] \
        + [dict(kind="egofb", q=q) for q in [0.1, 0.25, 0.5]] + [dict(kind="er", n=2000, d=d) for d in [5, 20]]
    outs = [dict(kappa=1.0, shape="concave"), dict(kappa=1.0, shape="convex"), dict(kappa=1.0, shape="thresh"),
            dict(kappa=1.0, shape="convex", het_gamma=0.5), dict(kappa=1.0, shape="concave", het_gamma=0.5), dict(kind="count")]
    for g, p, o in itertools.product(graphs, [0.25, 0.5], outs):
        cells.append(_cell(g, dict(o, gamma=1.0, sigma=0.5), dict(kind="bern", p=p), regs=["REG-L", "REG-Q", "REG-G", "REG-O"],
                           n_rep=R, sandwich=True, diag="no-boot", d4=True, theory_M=0, tag="e12"))
    return cells


def e9_intervals(R=100):
    """Variance estimators for REG-L as n grows at fixed d (effective independent units n / ball2 grows): exact-model slice and a misspecified one."""
    cells = []
    outs = [dict(kappa=0.0, gamma=1.0, sigma=1.0),                       # exact model
            dict(kappa=1.0, shape="convex", gamma=1.0, sigma=0.5)]       # misspecified: residuals depend on the neighbourhood
    for kind, n, d, o in itertools.product(["er", "sbm", "ba"], [2000, 4000, 8000, 16000], [10, 40], outs):
        cells.append(_cell(dict(kind=kind, n=n, d=d), o, dict(kind="bern", p=0.5), regs=["REG-L"], n_rep=R, sandwich=True,
                           intervals=dict(B=100), tag="e9"))
    return cells


def e10_assign_only(R=500):
    """Design-based variance: graph, frozen heterogeneity and noise fixed per cell, only the assignment redrawn.
    sd(tau_hat) over replicates is then the pure design sd; which standard error recovers it (and the iid-residual 2-9x gap)?"""
    cells = []
    outs = [dict(kappa=0.0, gamma=1.0, sigma=1.0),
            dict(kappa=0.0, gamma=1.0, sigma=0.0, sigma_alpha=0.5, w2=0.5),
            dict(kappa=1.0, shape="convex", gamma=1.0, sigma=0.0, sigma_alpha=0.5),
            dict(kappa=1.0, shape="thresh", gamma=1.0, sigma=0.0, sigma_alpha=0.5)]
    for kind, d, p, o in itertools.product(["er", "sbm", "ba", "ws"], [5, 10, 20, 40], [0.2, 0.5], outs):
        cells.append(_cell(dict(kind=kind, n=2000, d=d), o, dict(kind="bern", p=p), regs=["REG-L"], n_rep=R, sandwich=True,
                           intervals=dict(B=100), assign_only=True, tag="e10"))
    return cells


def e3c_relaxed(R=300):
    """Relaxed-exposure Hajek at more delta on the SAME draws as e3 (seed_cfg = the e3 cell)."""
    cells = []
    for c in e3_crossover(R):
        c2 = dict(c, seed_cfg=c, ht_deltas=[0.1, 0.25, 0.5, 0.75], ht_exact=False, theory_M=0, regs=["REG-L"], tag="e3c")
        cells.append(c2)
    return cells


MECH = {
    "linear": dict(kappa=0.0),
    "concave": dict(kappa=1.0, shape="concave"),
    "convex": dict(kappa=1.0, shape="convex"),
    "threshold": dict(kappa=1.0, shape="thresh", theta=0.5),
    "contagion": dict(kappa=1.0, shape="thresh", theta=0.3),
    "2hop-linear": dict(kappa=0.0, w2=0.5),
    "2hop-convex": dict(kappa=1.0, shape="convex", w2=0.5),
    "count": dict(kind="count"),
    "het-direct": dict(kappa=0.5, shape="convex", het_beta=0.5),
    "het-indirect": dict(kappa=0.5, shape="convex", het_gamma=0.5),
}


def e5_gcr(R=150):
    """C7: GCR cluster scale (Louvain resolution) on graphs with and without community structure."""
    cells = []
    graphs = [dict(kind="sbm", n=2000, d=20, kw=dict(mu=0.8)), dict(kind="sbm", n=2000, d=20, kw=dict(mu=0.5)),
              dict(kind="ws", n=2000, d=20, kw=dict(rewire=0.05)), dict(kind="er", n=2000, d=20)]
    outs = {k: dict(MECH[k], gamma=1.0, sigma=0.5) for k in ["linear", "convex", "threshold", "2hop-convex"]}
    for g, res, (mn, o) in itertools.product(graphs, [0.7, 1.0, 2.0, 5.0, 15.0, 50.0], outs.items()):
        cells.append(_cell(g, dict(o, shape=o.get("shape", "convex")), dict(kind="gcr", p=0.5, res=res),
                           regs=["REG-L", "REG-Q", "REG-O"], ht=True, ht_deltas=[0.25], n_rep=R, theory_M=10, tag=mn))
    # Bernoulli reference for each graph/mechanism
    for g, (mn, o) in itertools.product(graphs, outs.items()):
        cells.append(_cell(g, dict(o, shape=o.get("shape", "convex")), dict(kind="bern", p=0.5),
                           regs=["REG-L", "REG-Q", "REG-O"], ht=True, ht_deltas=[0.25], n_rep=R, theory_M=10, tag=mn))
    return cells


def e6_mechanisms(R=100):
    """C5: method x mechanism x graph map at p=0.5, n=2000, d=20 (real graph thinned)."""
    cells = []
    graphs = [dict(kind="er", n=2000, d=20), dict(kind="sbm", n=2000, d=20, kw=dict(mu=0.7)), dict(kind="ba", n=2000, d=20),
              dict(kind="ws", n=2000, d=20), dict(kind="egofb", q=0.5), dict(kind="stanford3", q=0.2)]
    for g, (mn, o) in itertools.product(graphs, MECH.items()):
        ml = ["gbm", "gcn"] if g["kind"] != "stanford3" else ["gbm"]
        cells.append(_cell(g, dict(o, gamma=1.0, sigma=0.5, shape=o.get("shape", "convex")), dict(kind="bern", p=0.5),
                           regs=["REG-L", "REG-Lc", "REG-Q", "REG-G", "REG-O"], ht=True, ht_deltas=[0.25], ml=ml,
                           n_rep=R, theory_M=10, tag=mn))
    return cells


def e11_observed_graph(R=100):
    """H4/C5: the analyst's graph has a fraction q of its edges wrong (same number dropped and added at random); outcomes follow the
    true graph with 1-hop (w2=0) or half-2-hop (w2=0.5) interference. Regressions build their exposure from the observed graph."""
    cells = []
    outs = {"linear": dict(kappa=0.0), "convex": dict(kappa=1.0, shape="convex")}
    graphs = [dict(kind="er", n=2000, d=20), dict(kind="sbm", n=2000, d=20, kw=dict(mu=0.7)), dict(kind="ba", n=2000, d=20),
              dict(kind="ws", n=2000, d=20)]
    for g, q, w2, (mn, o) in itertools.product(graphs, [0.0, 0.1, 0.25, 0.5, 0.75], [0.0, 0.5], outs.items()):
        cells.append(_cell(g, dict(o, gamma=1.0, sigma=0.5, w2=w2, shape=o.get("shape", "convex")), dict(kind="bern", p=0.5),
                           regs=["REG-L", "REG-Q", "REG-G", "REG-O"], obs=dict(q=q), n_rep=R, theory_M=10, tag=mn))
    return cells


def e8_stag(R=150):
    cells = []
    for T, d, mn in itertools.product([2, 4, 8], [10, 40], ["linear", "convex", "threshold", "2hop-convex"]):
        o = dict(MECH[mn], gamma=1.0, sigma=0.5, shape=MECH[mn].get("shape", "convex"))
        cells.append(_cell(dict(kind="er", n=2000, d=d), o, dict(kind="bern", p=0.5), regs=["REG-L"], stag=dict(T=T),
                           n_rep=R, tag=mn))
    return cells


GRIDS = dict(e12=e12_transport, e11=e11_observed_graph, e10=e10_assign_only, e9=e9_intervals, e3c=e3c_relaxed, e5=e5_gcr, e6=e6_mechanisms, e8=e8_stag, e7=e7_diagnostic, e4=e4_collapse, e1=e1_iid_slice, e1b=e1b_graphs, e2=e2_bias, e2b=e2b_plateau, e3=e3_crossover)
