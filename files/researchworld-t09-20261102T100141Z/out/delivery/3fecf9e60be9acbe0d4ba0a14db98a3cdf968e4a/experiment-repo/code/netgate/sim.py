"""Run one simulation cell: G graph draws x R assignments, all estimators on the same (z, y)."""
import hashlib, json, time
import numpy as np, pandas as pd, scipy.sparse as sp
from .graphs import make_graph, Net
from .outcomes import Outcome
from .designs import Design
from . import estimators as E

SE_OK = {"ols_f", "ols_cnt", "ols_f2", "ols_poly", "ols_f_adj", "ols_f_deg", "ols_f_both", "ols_cnt_adj", "ols_poly3", "ols_z"}


def cell_id(spec):
    return hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:10]


def perturb(net, rate, rng):
    """Observed graph with misspecified edges: drop a fraction `rate` of true edges and add the same number of random
    non-edges (so the edge count is preserved). Isolated nodes get one random edge (features need deg>0)."""
    A = sp.triu(net.A, 1).tocoo()
    m = A.nnz
    keep = rng.random(m) >= rate
    r, c = A.row[keep], A.col[keep]
    k = m - keep.sum()
    ar, ac = rng.integers(0, net.n, k), rng.integers(0, net.n, k)
    ok = ar != ac
    r = np.concatenate([r, ar[ok]]); c = np.concatenate([c, ac[ok]])
    B = sp.coo_matrix((np.ones(len(r)), (r, c)), shape=net.A.shape)
    B = ((B + B.T) > 0).astype(float).tocsr()
    iso = np.where(np.asarray(B.sum(1)).ravel() == 0)[0]
    if len(iso):
        j = rng.integers(0, net.n, len(iso)); j = np.where(j == iso, (j + 1) % net.n, j)
        B = B + sp.coo_matrix((np.ones(len(iso)), (iso, j)), shape=B.shape)
        B = ((B + B.T) > 0).astype(float).tocsr()
    return Net(B, net.name + f"_pert{rate}")


def theory_sd(net, base, sigma_e, p):
    """Design-based asymptotic SD of the OLS(z, f) GATE estimator under Bernoulli(p), linear-in-f truth:
    Var = [ ||b + dH W^T b||^2 / n + sigma_e^2 (1 + dH) ] / (n p (1-p)),  b = centred fixed baseline,
    dH = harmonic mean degree.  (Derivation in code/docs/THEORY.md.)"""
    n = net.n
    dH = 1.0 / np.mean(1.0 / net.deg)
    b = base - base.mean()
    v = b + dH * (net.W.T @ b)
    return float(np.sqrt((v @ v / n + sigma_e**2 * (1 + dH)) / (n * p * (1 - p))))


def setup_graph(spec, g, base_seed=20261102):
    """Deterministically rebuild graph draw g of a cell (graph, baseline/outcome object, GATE, RNG streams)."""
    cid = cell_id(spec)
    gs = spec["graph"]
    ss = np.random.SeedSequence([base_seed, int(cid, 16) % (2**31), g])
    r_graph, r_out, r_sim, r_pert = [np.random.default_rng(s) for s in ss.spawn(4)]
    net = make_graph(gs["kind"], gs.get("n", 0), int(r_graph.integers(2**31)), **{k: v for k, v in gs.items() if k not in ("kind", "n")})
    E.prep(net)
    comm = net.communities(1.0, 0)
    out = Outcome(**spec["outcome"]).setup(net, comm, r_out)
    return net, out, out.gate(), r_sim, r_pert, comm


def run_cell(spec, base_seed=20261102):
    """spec: dict(graph={kind,n,...}, outcome={...}, design={kind,p,res}, ests=[...], G=int, R=int, se=bool,
    pop=bool (also fit on the noise-free, baseline-free signal -> approximation error, names `<est>@pop`),
    graph_err=float (feature graph perturbed at this rate))."""
    cid = cell_id(spec)
    gs = spec["graph"]
    rows = []
    t0 = time.time()
    for g in range(spec.get("G", 1)):
        net, out, gate, r_sim, r_pert, comm = setup_graph(spec, g, base_seed)
        ds = spec["design"]
        labels = net.communities(ds.get("res", 1.0), 0) if ds["kind"] == "cluster" else None
        des = Design(ds["kind"], ds["p"], net, labels)
        fnet = net
        th = theory_sd(net, out.base, out.sigma_e, ds["p"]) if ds["kind"] == "bernoulli" else np.nan
        if spec.get("graph_err", 0) > 0:
            fnet = perturb(net, spec["graph_err"], r_pert)
            E.prep(fnet)
        for r in range(spec["R"]):
            z = des.draw(r_sim)
            if z.min() == z.max():
                continue
            y = out.observe(z, r_sim)
            f = fnet.W @ z
            diag = (float(f.mean()), float(f.std()), float((f >= 0.9).mean()), float((f <= 0.1).mean()))
            ysig = out.signal(z) if spec.get("pop") else None
            for name in spec["ests"]:
                se = np.nan
                if name == "dm":
                    est = E.diff_in_means(z, y)
                elif name == "hajek":
                    est = E.hajek_exposure(fnet, des, z, y)
                elif name.startswith("hajek_q"):
                    est = E.hajek_q(fnet, des, z, y, float(name[7:] or 0.75))
                else:
                    want = spec.get("se", False) and name in SE_OK
                    est, se = E.regression_gate(fnet, z, y, name, labels=comm if spec.get("se_cluster", True) else None, want_se=want)
                rows.append((cid, g, r, name, est, gate, se, net.n, net.deg.mean()) + diag + (th,))
                if ysig is not None and name not in ("hajek",) and not name.startswith("hajek_q"):
                    if name == "dm":
                        e2 = E.diff_in_means(z, ysig)
                    else:
                        e2, _ = E.regression_gate(fnet, z, ysig, name)
                    rows.append((cid, g, r, name + "@pop", e2, gate, np.nan, net.n, net.deg.mean()) + diag + (th,))
    df = pd.DataFrame(rows, columns=["cell", "g", "rep", "est_name", "est", "gate", "se", "n", "dbar",
                                     "f_mean", "f_sd", "ov1", "ov0", "th_sd"])
    df.attrs["secs"] = time.time() - t0
    return df
