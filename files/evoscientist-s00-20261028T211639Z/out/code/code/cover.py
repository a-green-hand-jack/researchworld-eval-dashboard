"""Monte Carlo study: predicting worst-start cover time of small graphs (n<=30)
from a few cheap graph statistics, compared against classical upper bounds.

Usage:  python code/cover.py            (writes results/ and paper/figs/)
Master seed: 2026. Per-graph seeds are derived deterministically from it.
"""
import json, math, os, sys, time
from multiprocessing import Pool
import numpy as np
import networkx as nx

MASTER_SEED = 2026
R1 = 256     # walks per start vertex in stage 1 (worst-start selection)
R2 = 2000    # fresh walks at the selected start in stage 2 (estimate)
SIZES = [8, 12, 16, 20, 24, 30]
N_RAND = 3   # instances per size for random families
OUT = os.path.join(os.path.dirname(__file__), "..", "results")
FIG = os.path.join(os.path.dirname(__file__), "..", "paper", "figs")


# ---------------------------------------------------------------- graphs
def build_graphs():
    rng = np.random.default_rng(MASTER_SEED)
    gs = []
    def add(fam, G):
        G = nx.convert_node_labels_to_integers(G)
        assert nx.is_connected(G) and G.number_of_nodes() <= 30
        gs.append((fam, G))
    grids = {8: (2, 4), 12: (3, 4), 16: (4, 4), 20: (4, 5), 24: (4, 6), 30: (5, 6)}
    for n in SIZES:
        add("path", nx.path_graph(n))
        add("cycle", nx.cycle_graph(n))
        add("star", nx.star_graph(n - 1))
        add("complete", nx.complete_graph(n))
        add("wheel", nx.wheel_graph(n))
        add("bipartite", nx.complete_bipartite_graph(n // 2, n - n // 2))
        add("grid", nx.grid_2d_graph(*grids[n]))
        k = n // 2
        add("lollipop", nx.lollipop_graph(k, n - k))       # clique K_k + path
        add("barbell", nx.barbell_graph(n // 3, n - 2 * (n // 3)))
        for _ in range(N_RAND):
            s = int(rng.integers(2**31))
            add("tree", nx.random_labeled_tree(n, seed=s))
            for fam, p in (("er_sparse", 2 * math.log(n) / n), ("er_dense", 0.5)):
                while True:
                    G = nx.gnp_random_graph(n, min(p, 1.0), seed=s); s += 1
                    if nx.is_connected(G): break
                add(fam, G)
            while True:
                G = nx.random_regular_graph(3, n, seed=s); s += 1
                if nx.is_connected(G): break
            add("3regular", G)
    return gs


# ---------------------------------------------------------------- simulation
def simulate(nbr, deg, start, R, rng):
    """R independent simple random walks from `start`; returns cover steps."""
    n = len(deg)
    cur = np.full(R, start, dtype=np.int64)
    vis = np.zeros((R, n), dtype=bool); vis[:, start] = True
    cnt = np.ones(R, dtype=np.int64)
    out = np.zeros(R, dtype=np.int64)
    alive = np.arange(R); t = 0
    while alive.size:
        t += 1
        c = cur[alive]
        nxt = nbr[c, (rng.random(alive.size) * deg[c]).astype(np.int64)]
        cur[alive] = nxt
        new = ~vis[alive, nxt]
        vis[alive[new], nxt[new]] = True
        cnt[alive] += new
        done = cnt[alive] == n
        out[alive[done]] = t
        alive = alive[~done]
    return out


def hitting_times(G):
    """Exact H[u,v] = expected hitting time of v from u (linear solves)."""
    n = G.number_of_nodes()
    A = nx.to_numpy_array(G, nodelist=range(n))
    P = A / A.sum(1, keepdims=True)
    H = np.zeros((n, n))
    for v in range(n):
        idx = [i for i in range(n) if i != v]
        M = np.eye(n - 1) - P[np.ix_(idx, idx)]
        H[idx, v] = np.linalg.solve(M, np.ones(n - 1))
    return H


def run_graph(args):
    gid, fam, edges, n = args
    G = nx.Graph(); G.add_nodes_from(range(n)); G.add_edges_from(edges)
    rng = np.random.default_rng([MASTER_SEED, gid])
    deg = np.array([G.degree(v) for v in range(n)])
    nbr = np.zeros((n, deg.max()), dtype=np.int64)
    for v in range(n):
        nb = sorted(G.neighbors(v)); nbr[v, :len(nb)] = nb
    # stage 1: all starts, pick empirical worst start
    s1 = np.array([simulate(nbr, deg, v, R1, rng).mean() for v in range(n)])
    vstar = int(np.argmax(s1))
    # stage 2: fresh walks at selected start -> unbiased estimate for that start
    x = simulate(nbr, deg, vstar, R2, rng)
    H = hitting_times(G)
    m = G.number_of_edges()
    Hn1 = sum(1.0 / k for k in range(1, n))
    return dict(gid=gid, family=fam, n=n, m=m, avg_deg=2 * m / n,
                max_deg=int(deg.max()), min_deg=int(deg.min()),
                diam=nx.diameter(G), start=vstar,
                cover=float(x.mean()), cover_se=float(x.std(ddof=1) / math.sqrt(R2)),
                cover_avgstart=float(s1.mean()),
                bound_akllr=2.0 * m * (n - 1),
                bound_feige_lead=4.0 / 27.0 * n ** 3,
                bound_matthews=float(H.max() * Hn1),
                lower_matthews=float(min(H[u, v] for u in range(n) for v in range(n) if u != v) * Hn1),
                Hmax=float(H.max()))


# ---------------------------------------------------------------- exact checks
def exact_checks(rows):
    """Closed-form worst-start cover times for path, cycle, complete graphs."""
    out = []
    for r in rows:
        n = r["n"]
        if r["family"] == "path":
            L = n - 1; k = r["start"]
            ex = k * (L - k) + L * L                  # exact from the selected start k
            exmax = (L // 2) * (L - L // 2) + L * L   # exact worst start (middle vertex)
        elif r["family"] == "cycle":
            ex = exmax = n * (n - 1) / 2
        elif r["family"] == "complete":
            ex = exmax = (n - 1) * sum(1.0 / k for k in range(1, n))
        else:
            continue
        z = (r["cover"] - ex) / r["cover_se"]
        out.append(dict(family=r["family"], n=n, exact=ex, mc=r["cover"], se=r["cover_se"], z=z,
                        selected_over_worst=ex / exmax))
    return out


# ---------------------------------------------------------------- prediction models
FEATS = {
    "M1: log(2m(n-1)) [calibrated AKLLR]": lambda r: [math.log(2 * r["m"] * (r["n"] - 1))],
    "M2: log(m D ln n)": lambda r: [math.log(r["m"] * r["diam"] * math.log(r["n"]))],
    "M3: log n, log m": lambda r: [math.log(r["n"]), math.log(r["m"])],
    "M4: log n, log m, log dmax, log D": lambda r: [math.log(r["n"]), math.log(r["m"]),
                                                     math.log(r["max_deg"]), math.log(r["diam"])],
}


def design(rows, f):
    return np.array([[1.0] + f(r) for r in rows])


def fit_predict(rows_tr, y_tr, rows_te, f):
    X = design(rows_tr, f)
    beta, *_ = np.linalg.lstsq(X, y_tr, rcond=None)
    return design(rows_te, f) @ beta, beta


def lofo_predictions(rows, y, f):
    """Leave-one-family-out: each family is predicted by a model never fit on it."""
    fams = sorted(set(r["family"] for r in rows))
    pred = np.zeros(len(rows))
    for fam in fams:
        te = [i for i, r in enumerate(rows) if r["family"] == fam]
        tr = [i for i, r in enumerate(rows) if r["family"] != fam]
        p, _ = fit_predict([rows[i] for i in tr], y[tr], [rows[i] for i in te], f)
        pred[te] = p
    return pred


def kfold_predictions(rows, y, f, k=5, seed=MASTER_SEED):
    idx = np.random.default_rng(seed).permutation(len(rows))
    pred = np.zeros(len(rows))
    for fold in np.array_split(idx, k):
        tr = np.setdiff1d(idx, fold)
        p, _ = fit_predict([rows[i] for i in tr], y[tr], [rows[i] for i in fold], f)
        pred[fold] = p
    return pred


def boot_ci(v, B=2000, seed=MASTER_SEED):
    rng = np.random.default_rng(seed)
    v = np.asarray(v)
    bs = [np.mean(v[rng.integers(0, len(v), len(v))]) for _ in range(B)]
    return float(np.mean(v)), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(FIG, exist_ok=True)
    t0 = time.time()
    gs = build_graphs()
    jobs = [(i, fam, list(G.edges()), G.number_of_nodes()) for i, (fam, G) in enumerate(gs)]
    with Pool(min(32, os.cpu_count() or 1)) as pool:
        rows = pool.map(run_graph, jobs)
    print(f"simulated {len(rows)} graphs in {time.time()-t0:.1f}s")
    json.dump(rows, open(os.path.join(OUT, "graphs.json"), "w"), indent=1)

    checks = exact_checks(rows)
    json.dump(checks, open(os.path.join(OUT, "exact_checks.json"), "w"), indent=1)
    zs = np.array([c["z"] for c in checks])
    print(f"exact checks: {len(zs)} graphs, max|z|={np.abs(zs).max():.2f}, mean z={zs.mean():.2f}")

    y = np.log([r["cover"] for r in rows])
    yse = np.array([r["cover_se"] / r["cover"] for r in rows])   # SE of log C (delta method)
    fams = sorted(set(r["family"] for r in rows))
    preds = {}
    for name, key in (("AKLLR 2m(n-1)", "bound_akllr"), ("Feige lead 4n^3/27", "bound_feige_lead"),
                      ("Matthews H_max*H_{n-1}", "bound_matthews")):
        preds["bound: " + name] = np.log([r[key] for r in rows])
    coefs = {}
    for name, f in FEATS.items():
        preds[name + " (LOFO)"] = lofo_predictions(rows, y, f)
        preds[name + " (5-fold)"] = kfold_predictions(rows, y, f)
        _, beta = fit_predict(rows, y, rows, f); coefs[name] = beta.tolist()

    # MC-uncertainty propagation: refit everything on targets resampled from N(mean,se)
    rng = np.random.default_rng(MASTER_SEED + 1)
    mc_rep = {name: [] for name in preds}
    for _ in range(200):
        yb = y + rng.normal(0, yse)
        for name in preds:
            if name.startswith("bound"):
                p = preds[name]
            else:
                base = name.rsplit(" (", 1)[0]; f = FEATS[base]
                p = lofo_predictions(rows, yb, f) if "LOFO" in name else kfold_predictions(rows, yb, f)
            mc_rep[name].append(np.mean(np.abs(p - yb)))

    summary = {}
    for name, p in preds.items():
        e = p - y                                   # log ratio predicted/true
        mae, lo, hi = boot_ci(np.abs(e))
        summary[name] = dict(mean_abs_log_err=mae, ci95=[lo, hi],
                             mc_sd_of_mae=float(np.std(mc_rep[name])),
                             median_ratio=float(np.exp(np.median(e))),
                             max_ratio=float(np.exp(e.max())), min_ratio=float(np.exp(e.min())),
                             frac_within_25pct=float(np.mean(np.abs(np.exp(e) - 1) <= 0.25)),
                             per_family={fam: float(np.mean([e[i] for i, r in enumerate(rows) if r["family"] == fam]))
                                         for fam in fams},
                             per_family_abs={fam: float(np.mean([abs(e[i]) for i, r in enumerate(rows) if r["family"] == fam]))
                                             for fam in fams})
    # drop-one-feature ablation of M4 (LOFO and 5-fold)
    base_f = {"log n": lambda r: math.log(r["n"]), "log m": lambda r: math.log(r["m"]),
              "log dmax": lambda r: math.log(r["max_deg"]), "log D": lambda r: math.log(r["diam"])}
    ablation = {}
    for drop in [None] + list(base_f):
        keep = [k for k in base_f if k != drop]
        f = (lambda ks: (lambda r: [base_f[k](r) for k in ks]))(keep)
        out = {}
        for cv, fn in (("LOFO", lofo_predictions), ("5-fold", kfold_predictions)):
            mae, lo, hi = boot_ci(np.abs(fn(rows, y, f) - y)); out[cv] = [mae, lo, hi]
        ablation["full M4" if drop is None else "drop " + drop] = out
    print("ablation:", json.dumps(ablation))
    res_ablation = ablation
    res = dict(ablation=res_ablation, n_graphs=len(rows), R1=R1, R2=R2, seed=MASTER_SEED,
               median_rel_se=float(np.median(yse)), max_rel_se=float(yse.max()),
               summary=summary, coefs_full_fit=coefs, feature_names={k: None for k in FEATS},
               exact_check_max_abs_z=float(np.abs(zs).max()), runtime_s=time.time() - t0)
    json.dump(res, open(os.path.join(OUT, "summary.json"), "w"), indent=1)
    for name, s in summary.items():
        print(f"{name:45s} MAE(log)={s['mean_abs_log_err']:.3f} [{s['ci95'][0]:.3f},{s['ci95'][1]:.3f}] "
              f"mcSD={s['mc_sd_of_mae']:.4f} med ratio={s['median_ratio']:.2f} within25%={s['frac_within_25pct']:.2f}")
    np.save(os.path.join(OUT, "preds.npy"), {k: v for k, v in preds.items()}, allow_pickle=True)
    make_figs(rows, y, preds, fams)
    write_tables(res, rows, fams)
    print(f"total runtime {time.time()-t0:.1f}s")


def make_figs(rows, y, preds, fams):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    best = "M4: log n, log m, log dmax, log D (LOFO)"
    cmap = plt.get_cmap("tab20")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for ax, key, title in ((axes[0], "bound: AKLLR 2m(n-1)", "Upper bound $2m(n-1)$"),
                           (axes[1], best, "M4 (leave-one-family-out)")):
        for j, fam in enumerate(fams):
            ii = [i for i, r in enumerate(rows) if r["family"] == fam]
            ax.scatter(np.exp(y[ii]), np.exp(preds[key][ii]), s=14, color=cmap(j), label=fam)
        lim = [np.exp(y).min() * 0.7, max(np.exp(y).max(), np.exp(preds[key]).max()) * 1.4]
        ax.plot(lim, lim, "k--", lw=0.8)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim)
        ax.set_xlabel("MC cover time (worst start)"); ax.set_ylabel("prediction"); ax.set_title(title)
    axes[1].legend(fontsize=6.5, ncol=2, loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "scatter.pdf")); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 3.2))
    keys = ["bound: AKLLR 2m(n-1)", "bound: Matthews H_max*H_{n-1}",
            "M1: log(2m(n-1)) [calibrated AKLLR] (LOFO)", best]
    labels = ["$2m(n-1)$", "Matthews", "M1 LOFO", "M4 LOFO"]
    w = 0.2
    for k, (key, lab) in enumerate(zip(keys, labels)):
        vals = [np.mean([preds[key][i] - y[i] for i, r in enumerate(rows) if r["family"] == fam]) for fam in fams]
        ax.bar(np.arange(len(fams)) + (k - 1.5) * w, vals, w, label=lab)
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xticks(np.arange(len(fams))); ax.set_xticklabels(fams, rotation=30, fontsize=8)
    ax.set_ylabel("mean log(pred/true)"); ax.legend(fontsize=7, ncol=4)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "family_bias.pdf")); plt.close(fig)


def write_tables(res, rows, fams):
    S = res["summary"]
    order = ["bound: AKLLR 2m(n-1)", "bound: Feige lead 4n^3/27", "bound: Matthews H_max*H_{n-1}"]
    for k in FEATS: order += [k + " (5-fold)", k + " (LOFO)"]
    lab = {"bound: AKLLR 2m(n-1)": "Bound $2m(n-1)$",
           "bound: Feige lead 4n^3/27": "Leading term $\\frac{4}{27}n^3$",
           "bound: Matthews H_max*H_{n-1}": "Matthews $H_{\\max} h_{n-1}$ (exact $H$)",
           "M1: log(2m(n-1)) [calibrated AKLLR]": "M1: $\\log 2m(n{-}1)$",
           "M2: log(m D ln n)": "M2: $\\log(mD\\ln n)$",
           "M3: log n, log m": "M3: $\\log n,\\log m$",
           "M4: log n, log m, log dmax, log D": "M4: $\\log n,\\log m,\\log d_{\\max},\\log D$"}
    def tex(s):
        if s in lab: return lab[s]
        base, cv = s.rsplit(" (", 1)
        return lab[base] + " (" + cv
    L = ["\\begin{tabular}{lcccc}", "\\toprule",
         "Predictor & MAE$_{\\log}$ [95\\% CI] & MC s.d. & median ratio & within 25\\% \\\\", "\\midrule"]
    for k in order:
        s = S[k]
        L.append(f"{tex(k)} & {s['mean_abs_log_err']:.3f} [{s['ci95'][0]:.3f}, {s['ci95'][1]:.3f}] & "
                 f"{s['mc_sd_of_mae']:.4f} & {s['median_ratio']:.2f} & {100*s['frac_within_25pct']:.0f}\\% \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(OUT, "table_main.tex"), "w").write("\n".join(L))
    best = "M4: log n, log m, log dmax, log D (LOFO)"
    kf = "M4: log n, log m, log dmax, log D (5-fold)"
    L = ["\\begin{tabular}{lccccc}", "\\toprule",
         "Family & \\#graphs & $2m(n-1)$ & Matthews & M4 5-fold & M4 LOFO \\\\", "\\midrule"]
    for fam in fams:
        cnt = sum(r["family"] == fam for r in rows)
        f = lambda k: math.exp(S[k]["per_family"][fam])
        L.append(f"{fam.replace('_', '-')} & {cnt} & {f('bound: AKLLR 2m(n-1)'):.2f} & "
                 f"{f('bound: Matthews H_max*H_{n-1}'):.2f} & {f(kf):.2f} & {f(best):.2f} \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(OUT, "table_family.tex"), "w").write("\n".join(L))


if __name__ == "__main__":
    main()
