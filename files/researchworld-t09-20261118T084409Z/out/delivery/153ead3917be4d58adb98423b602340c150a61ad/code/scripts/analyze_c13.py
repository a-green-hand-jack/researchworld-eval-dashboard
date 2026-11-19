"""M3 follow-up (review of the final candidate): why REG-L on the threshold response at theta = 0.5 is far better on ego-Facebook / Stanford3
(error 0.21 / 0.17) than on ER / SBM / BA / WS (0.53-0.64) in grid e6.  python scripts/analyze_c13.py   (needs the two graph files, NETGATE_DATA)
Writes results/summary/c13_exposure.csv (per graph: exact REG-L projection bias and the exposure support that explains it) and
c13_fit_subset.csv (the same bias when the regression is fitted only on units of a degree range).  No replicates: the quantities are design-exact
(the projection is a Monte Carlo over assignments only, M draws).
Hypothesis, stated before computing: OLS on (1, z, g) fits a slope on g that is local to where g has mass.  On a graph of degree ~20 at p = 0.5
g has sd ~0.11, concentrated at the step, so the fitted slope is the step's steepness and the corner extrapolation overshoots; units of low
degree have g spread over [0,1], put the two plateaus in the data, and pull the slope towards the chord.  It predicts that (a) the bias tracks the mass of
units whose g reaches a plateau (|g - 0.5| > 0.3), not degree heterogeneity as such (BA has heterogeneous degree but minimum degree 10);
(b) fitting only on units of degree >= 12 moves the real graphs towards the synthetic ones, fitting only on degree <= 5 moves the synthetic ones away."""
import numpy as np
import pandas as pd
from scipy.stats import binom

from netgate.ctx import Ctx
from netgate.designs import Design
from netgate.estimators import FEATURES
from netgate.grids import MECH
from netgate.graphs import make_graph
from netgate.outcomes import OutSpec, freeze, potential
from netgate.theory import projection

P = 0.5
GRAPHS = [("ER", dict(kind="er", n=2000, d=20)), ("SBM", dict(kind="sbm", n=2000, d=20, kw=dict(mu=0.7))), ("BA", dict(kind="ba", n=2000, d=20)),
          ("WS", dict(kind="ws", n=2000, d=20)), ("ego-Facebook", dict(kind="egofb", q=0.5)), ("Stanford3", dict(kind="stanford3", q=0.2))]
RESP = {"thresh .5": MECH["threshold"], "thresh .3": MECH["contagion"], "linear": MECH["linear"]}
M = 200


def build(g, seed):
    rng = np.random.default_rng(seed)
    kw = {k: v for k, v in g.items() if k not in ("kind", "n", "d", "kw")}
    A, b = make_graph(g["kind"], n=g.get("n", 2000), d=g.get("d", 20), rng=rng, **kw, **g.get("kw", {}))
    return Ctx(A, b)


def fit_bias(ctx, spec, mask, rng, M=M):
    """Exact (over the design) bias of REG-L when the regression is fitted on the units in `mask` and the corner is predicted over all units."""
    fz0 = dict(freeze(spec, ctx, np.random.default_rng(0)), alpha=np.zeros(ctx.n))
    c1, c0 = ctx.corner(1), ctx.corner(0)
    tau = float(np.mean(potential(spec, fz0, ctx, c1) - potential(spec, fz0, ctx, c0)))
    D = (FEATURES["REG-L"](c1, ctx, spec) - FEATURES["REG-L"](c0, ctx, spec)).mean(0)
    Mm, v, slope_pts = 0, 0, []
    for _ in range(M):
        st = ctx.state(Design("bern", P).draw(ctx.n, rng))
        Phi = FEATURES["REG-L"](st, ctx, spec)[mask]
        f = potential(spec, fz0, ctx, st)[mask]
        Mm = Mm + Phi.T @ Phi / mask.sum(); v = v + Phi.T @ f / mask.sum()
    beta = np.linalg.lstsq(Mm / M, v / M, rcond=None)[0]
    return float(D @ beta) - tau, float(beta[2]), tau


rows, rows2 = [], []
for name, g in GRAPHS:
    ctx = build(g, 7)
    deg = ctx.deg
    pl = np.mean(binom.cdf(np.floor(0.2 * deg), deg, P) + binom.sf(np.ceil(0.8 * deg) - 1, deg, P))       # P(g <= .2 or g >= .8)
    sd_g = float(np.sqrt(np.mean(P * (1 - P) / deg)))
    st = ctx.state(Design("bern", P).draw(ctx.n, np.random.default_rng(1)))
    for rn, o in RESP.items():
        spec = OutSpec(**dict(dict(gamma=1.0, sigma=0.0), **{k: v for k, v in o.items()}))
        rng = np.random.default_rng(11)
        pr = projection(["REG-L"], ctx, spec, dict(freeze(spec, ctx, np.random.default_rng(0))), Design("bern", P), rng, M=M)["REG-L"]
        b_all, slope, tau = fit_bias(ctx, spec, np.ones(ctx.n, bool), np.random.default_rng(11))
        rows.append(dict(graph=name, response=rn, n=ctx.n, d_mean=ctx.dbar, d_min=int(deg.min()), frac_deg_le5=float(np.mean(deg <= 5)), frac_deg_le10=float(np.mean(deg <= 10)),
                         sd_g=sd_g, plateau_mass=pl, bias_theory=pr["bias_pred"], bias_here=b_all, bias_norm=b_all / 2, slope_g=slope, tau=tau, L=pr["L"]))
        if rn == "thresh .5":
            for lab, mask in [("deg<=5", deg <= 5), ("deg 6-11", (deg >= 6) & (deg <= 11)), ("deg>=12", deg >= 12), ("deg>=20", deg >= 20)]:
                if mask.sum() < 50:
                    continue
                b, s, _ = fit_bias(ctx, spec, mask, np.random.default_rng(11))
                rows2.append(dict(graph=name, fit_on=lab, n_fit=int(mask.sum()), bias=b, bias_norm=b / 2, slope_g=s))
    print(name, "done", flush=True)
a = pd.DataFrame(rows); b = pd.DataFrame(rows2)
# measured REG-L bias in grid e6 (threshold .5, Bernoulli p = .5) beside the exact value computed here (independent graph draws for the synthetic families)
e6 = pd.read_csv("results/summary/e6.csv")
e6 = e6[(e6.est == "REG-L") & (e6["out.shape"] == "thresh") & (e6["out.theta"] == 0.5) & (e6["out.kappa"] == 1)]
key = {"er": "ER", "sbm": "SBM", "ba": "BA", "ws": "WS", "egofb": "ego-Facebook", "stanford3": "Stanford3"}
m = {key[r["graph.kind"]]: (r.bias, r.bias_se) for _, r in e6.iterrows()}
a["bias_e6_measured"] = [m[g][0] if r == "thresh .5" else np.nan for g, r in zip(a.graph, a.response)]
a["bias_e6_se"] = [m[g][1] if r == "thresh .5" else np.nan for g, r in zip(a.graph, a.response)]
r5 = a[a.response == "thresh .5"]
print("plateau mass vs exact bias, 6 graphs: Spearman", pd.Series(r5.plateau_mass.values).corr(pd.Series(r5.bias_theory.values), method="spearman"))
a.to_csv("results/summary/c13_exposure.csv", index=False); b.to_csv("results/summary/c13_fit_subset.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(a.round(3).to_string()); print(b.round(3).to_string())
