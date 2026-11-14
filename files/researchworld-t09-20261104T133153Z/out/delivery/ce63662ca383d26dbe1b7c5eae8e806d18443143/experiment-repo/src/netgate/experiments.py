"""Experiment grids. Each experiment is a list of cell configs for runner.run_cell.
Defaults: tau=1, sigma=1; worlds draw baseline+noise (and the graph, for synthetic graphs)."""
import itertools

SBM = "sbm:5000,50,20,0.8"
SYN = {"sbm": SBM, "ba": "ba:5000,10", "ws": "ws:5000,20,0.1", "er": "er:5000,20"}
REAL = {"stanford3": "stanford3", "ego": "ego"}
ALL_G = {**SYN, **REAL}
SPECS = ["OLS_f", "OLS_zf", "OLS_cnt", "OLS_fd", "OLS_f2", "OLS_quad", "OLS_cubic", "OLS_big", "ORACLE", "ORACLE_D"]


def _w(gname, scale=1):
    """worlds, reps: real graphs are fixed so draw baselines (worlds) x assignments."""
    return (4, 100 * scale) if gname in SYN else (4, 100 * scale)


def cell(graph, design, outcome, worlds, reps, tag, seed, **kw):
    return dict(graph=graph, design=design, outcome=outcome, worlds=worlds, reps=reps, tag=tag, seed=seed, **kw)


def e1_interference_strength():
    """Bias/RMSE vs interference strength gamma, linear-in-means truth, all graphs, two designs."""
    out, s = [], 100
    for gn, gs in ALL_G.items():
        for des in ["bern:0.5", "louv:1.0,0.5"]:
            for gamma in [0.0, 0.5, 1.0, 2.0, 4.0]:
                s += 1
                out.append(cell(gs, des, dict(mech="shape", kind="linear", gamma=gamma), *_w(gn), f"{gn}", s, specs=SPECS))
    return out


def e2_misspecification():
    """Nonlinear spillover shapes: does the linear exposure regression extrapolate correctly?"""
    out, s = [], 200
    for gn, gs in ALL_G.items():
        for kind in ["linear", "concave", "convex", "sigmoid"]:
            for des in ["bern:0.5", "bern:0.1", "louv:1.0,0.5", "rand:1.0,0.5"]:
                s += 1
                out.append(cell(gs, des, dict(mech="shape", kind=kind, gamma=2.0), *_w(gn), f"{gn}", s, specs=SPECS, gbm=True))
    return out


def e3_scaling():
    """SD of the estimator vs n and mean degree (SBM, ER and BA), Bernoulli(0.5), linear truth."""
    out, s = [], 300
    for n in [1000, 2000, 5000, 10000, 20000]:
        for d in [5, 10, 20, 40, 80]:
            s += 1
            out.append(cell(f"er:{n},{d}", "bern:0.5", dict(mech="shape", kind="linear", gamma=1.0), 4, 100, "er", s,
                            specs=["OLS_f", "OLS_zf", "OLS_fd", "OLS_big", "ORACLE"], hajek=False))
            s += 1
            out.append(cell(f"sbm:{n},{max(n // 100, 5)},{d},0.8", "louv:1.0,0.5", dict(mech="shape", kind="linear", gamma=1.0), 4, 100, "sbm_louv", s,
                            specs=["OLS_f", "OLS_zf", "OLS_fd", "OLS_big", "ORACLE"], hajek=False))
    for n in [1000, 5000, 20000]:
        for m in [2, 5, 10, 20]:
            s += 1
            out.append(cell(f"ba:{n},{m}", "bern:0.5", dict(mech="shape", kind="linear", gamma=1.0), 4, 100, "ba", s,
                            specs=["OLS_f", "OLS_fd", "ORACLE"], hajek=False))
    return out


def e4_design():
    """Treatment probability, cluster resolution, cluster quality (planted in_frac), random-cluster control."""
    out, s = [], 400
    for gn in ["sbm", "stanford3", "ego"]:
        gs = ALL_G[gn]
        for kind in ["linear", "concave"]:
            o = dict(mech="shape", kind=kind, gamma=2.0)
            for p in [0.05, 0.1, 0.25, 0.5]:
                s += 1
                out.append(cell(gs, f"bern:{p}", o, 4, 100, f"{gn}|bern_p", s, specs=SPECS))
            for res in [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]:
                for kd in ["louv", "rand"]:
                    s += 1
                    out.append(cell(gs, f"{kd}:{res},0.5", o, 4, 100, f"{gn}|{kd}_res", s, specs=SPECS))
    for f in [0.5, 0.7, 0.8, 0.9, 0.97]:
        for kind in ["linear", "concave"]:
            o = dict(mech="shape", kind=kind, gamma=2.0)
            for des in ["bern:0.5", "block:0.5", "louv:1.0,0.5"]:
                s += 1
                out.append(cell(f"sbm:5000,50,20,{f}", des, o, 4, 100, f"sbm_f{f}", s, specs=SPECS))
    return out


def e5_noise_baseline():
    out, s = [], 500
    for gn in ["sbm", "stanford3"]:
        for sigma in [0.25, 1.0, 4.0]:
            for ag in [0.0, 1.0, 3.0]:
                for des in ["bern:0.5", "louv:1.0,0.5"]:
                    s += 1
                    out.append(cell(ALL_G[gn], des, dict(mech="shape", kind="linear", gamma=1.0, sigma=sigma, alpha_graph=ag), 4, 100, gn, s,
                                    specs=["OLS_f", "OLS_fd", "ORACLE"], hajek=False))
    return out


def e7_mechanisms():
    """Other interference mechanisms and the feature-set ablation."""
    out, s = [], 700
    mechs = [dict(mech="count", gamma=2.0), dict(mech="twohop", gamma=1.0, gamma2=1.0), dict(mech="hetero", gamma=2.0),
             dict(mech="prop", rho=0.3), dict(mech="prop", rho=0.6), dict(mech="prop", rho=0.9)]
    for gn, gs in ALL_G.items():
        for m in mechs:
            for des in ["bern:0.5", "louv:1.0,0.5"]:
                s += 1
                out.append(cell(gs, des, m, 4, 100, gn, s, specs=SPECS, gbm=True))
    return out


NOISELESS = dict(sigma=0.0, alpha_graph=0.0, alpha_deg=0.0, alpha_iid=0.0)


def e6_inference():
    """Coverage of 95% CIs (HC0, cluster-robust at several analysis resolutions, graph-HAC) for OLS_f / OLS_fd."""
    out, s = [], 600
    for gn, gs in ALL_G.items():
        for kind in ["linear", "concave"]:
            for des in ["bern:0.5", "louv:1.0,0.5"]:
                for acl in ([0.5, 1.0, 2.0, 5.0] if des.startswith("bern") else [1.0]):
                    s += 1
                    out.append(cell(gs, des, dict(mech="shape", kind=kind, gamma=2.0), 4, 150, f"{gn}|acl{acl}", s,
                                    specs=["OLS_f", "OLS_fd", "OLS_quad", "ORACLE_D"], hajek=False, acl_res=acl))
    return out


def e8_noiseless_bias():
    """Pure specification/extrapolation bias: noiseless outcomes (no baseline, no noise), mean over assignments."""
    out, s = [], 800
    for gn, gs in ALL_G.items():
        for kind in ["linear", "concave", "convex", "sigmoid"]:
            for des in ["bern:0.5", "bern:0.1", "bern:0.9", "louv:1.0,0.5", "rand:1.0,0.5"]:
                s += 1
                out.append(cell(gs, des, dict(mech="shape", kind=kind, gamma=2.0, **NOISELESS), 2, 60, gn, s, specs=SPECS, gbm=True))
    return out


def e9_curvature():
    """Noiseless bias vs spillover curvature and treatment probability (compare with the closed-form prediction)."""
    out, s = [], 900
    for gn in ["sbm", "ba", "stanford3"]:
        for kind in ["concave", "convex"]:
            for curv in [0.5, 1.0, 2.0, 3.0, 5.0, 8.0]:
                for p in [0.1, 0.25, 0.5, 0.75]:
                    s += 1
                    out.append(cell(ALL_G[gn], f"bern:{p}", dict(mech="shape", kind=kind, curv=curv, gamma=2.0, **NOISELESS), 2, 50,
                                    f"{gn}", s, specs=["OLS_f", "OLS_zf", "OLS_quad", "OLS_cubic", "ORACLE"], gbm=False, hajek=False))
    return out


def e10_bias_vs_n():
    """H3: does misspecification bias shrink with n? concave spillover, SBM (mean degree 20, ~100 nodes per block), Bernoulli and Louvain-cluster designs."""
    out, s = [], 1000
    for n in [1000, 2000, 5000, 10000, 20000]:
        for kind in ["linear", "concave"]:
            for des in ["bern:0.5", "bern:0.1", "louv:1.0,0.5"]:
                s += 1
                out.append(cell(f"sbm:{n},{max(n // 100, 5)},20,0.8", des, dict(mech="shape", kind=kind, gamma=2.0), 4, 100, f"n{n}", s,
                                specs=["OLS_f", "OLS_quad", "ORACLE_D"], hajek=False))
    return out


def e11_gamma_misspecified():
    """Added after the freeze (H3, gamma-dependence). Noisy outcomes; concave and sigmoid spillover, gamma varies, Bernoulli designs.
    Prediction: the bias of OLS_f is proportional to gamma, since the baseline and noise do not depend on gamma and
    the OLS estimator is linear in y."""
    out, s = [], 1100
    for gn in ["sbm", "ba", "stanford3", "ego"]:
        for kind in ["concave", "sigmoid"]:
            for des in ["bern:0.5", "bern:0.1"]:
                for gamma in [0.5, 1.0, 2.0, 4.0]:
                    s += 1
                    out.append(cell(ALL_G[gn], des, dict(mech="shape", kind=kind, gamma=gamma), 4, 100, gn, s,
                                    specs=["OLS_f", "OLS_quad", "ORACLE_D"], hajek=False))
    return out


def e12_hajek():
    """Added after the freeze (H6, exposure-mapping baselines). Low-degree graphs (n = 3000) where full / kappa exposure
    occurs; mechanisms for which the exposure mapping is correct (step, kappa = 1 and 0.75) and wrong (linear, sigmoid,
    two-hop, propagation). HajekKappa(0.75) exists for Bernoulli designs only. 'step' oracles use 1[f >= kappa]."""
    out, s = [], 1200
    graphs = {"er4": "er:3000,4", "er8": "er:3000,8", "ws4": "ws:3000,4,0.1", "ws8": "ws:3000,8,0.1", "ba2": "ba:3000,2", "ba4": "ba:3000,4"}
    mechs = [dict(mech="step", kappa=1.0, gamma=2.0), dict(mech="step", kappa=0.75, gamma=2.0),
             dict(mech="shape", kind="linear", gamma=2.0), dict(mech="shape", kind="sigmoid", gamma=2.0),
             dict(mech="twohop", gamma=1.0, gamma2=1.0), dict(mech="prop", rho=0.6)]
    for gn, gs in graphs.items():
        for m in mechs:
            for des in ["bern:0.5", "bern:0.8", "louv:1.0,0.5"]:
                s += 1
                out.append(cell(gs, des, m, 4, 100, gn, s, specs=["OLS_f", "ORACLE", "ORACLE_D"], hajek=True))
    return out


def e13_second_seed():
    """Added after the freeze: second seed (original seed + 10000) of the cells behind three headline verdicts: H5 (e4, Stanford3 and
    ego-Facebook Louvain vs random clusters, all resolutions), H2 (all e9 cells) and H4 (the ER Bernoulli(0.5) part of e3)."""
    out = []
    for c in e4_design():
        if c["graph"] in ("stanford3", "ego") and c["design"].split(":")[0] in ("louv", "rand"):
            out.append({**c, "seed": c["seed"] + 10000, "tag": "seed2|" + c["tag"]})
    for c in e9_curvature():
        out.append({**c, "seed": c["seed"] + 10000, "tag": "seed2|" + c["tag"]})
    for c in e3_scaling():
        if c["graph"].startswith("er:"):
            out.append({**c, "seed": c["seed"] + 10000, "tag": "seed2|" + c["tag"]})
    return out


# ---- grids added after the freeze, in answer to the review requests of paper-repo (experiment-repo#11-#16) ----
FAST = dict(no_acl=True, hac=False, hajek=False)   # point estimates only: no analysis clusters, no graph-HAC, no Hajek


def e14_matched_heavy_tail():
    """experiment-repo#11. Graphs that differ only in the degree distribution at n = 5000 and mean degree ~ 20: BA(10), the configuration model
    on the BA degree sequence, ER, a 20-regular graph and shifted power laws (exponent 2.2, 2.5, 3.0, degrees <= 500). Bernoulli(0.5), linear and
    concave truth, gamma = 0 and 2, noisy; 8 worlds (a new graph each) x 50 assignments."""
    out, s = [], 1400
    graphs = {"ba": "ba:5000,10", "cmba": "cmba:5000,10", "er": "er:5000,20", "reg": "reg:5000,20",
              "pl2.2": "pl:5000,2.2,20", "pl2.5": "pl:5000,2.5,20", "pl3.0": "pl:5000,3.0,20"}
    for gn, gs in graphs.items():
        for kind in ["linear", "concave"]:
            for gamma in [0.0, 2.0]:
                s += 1
                out.append(cell(gs, "bern:0.5", dict(mech="shape", kind=kind, gamma=gamma), 8, 50, gn, s,
                                specs=["OLS_f", "OLS_fd", "ORACLE", "ORACLE_D"], **FAST))
    return out


def e15_coverage():
    """experiment-repo#12. Coverage of the GATE and of E[tau-hat] for HC0 / cluster-robust / graph-HAC-1 / graph-HAC-2 (dense kernel on Stanford3)
    and the Louvain block bootstrap (B = 200, percentile and SD) of OLS_f; all six graphs, Bernoulli(0.5) (analysis clusters: Louvain resolution 1)
    and Louvain-cluster designs (analysis clusters = design clusters); linear and concave truth, gamma = 2; 4 worlds x 150 assignments."""
    out, s = [], 1500
    for gn, gs in ALL_G.items():
        for kind in ["linear", "concave"]:
            for des in ["bern:0.5", "louv:1.0,0.5"]:
                s += 1
                out.append(cell(gs, des, dict(mech="shape", kind=kind, gamma=2.0), 4, 150, f"{gn}|boot", s,
                                specs=["OLS_f", "ORACLE_D"], hajek=False, boot=200, dense_k2=(gn == "stanford3"), acl_res=1.0))
    return out


def e16_estimator_scope():
    """experiment-repo#13. The Bernoulli cells of e2 (same seeds, so the same worlds and assignments) with the separate-arm specification
    (OLS_zf, i.e. z, f, z*f), ridge and lasso-selected versions of the 11-column feature set, and a cross-validated GBM (on the Bernoulli(0.5) cells)."""
    out = []
    for c in e2_misspecification():
        if not c["design"].startswith("bern"):
            continue
        extra = ["RIDGE_big", "LASSO_big"] + (["GBM_tuned"] if c["design"] == "bern:0.5" else [])
        out.append({**c, "specs": ["OLS_f", "OLS_zf", "OLS_big"], "extra": extra, "gbm": True, **FAST})
    return out


def e17_crossover():
    """experiment-repo#14(1). SBM (n/100 blocks, 80% in-block edges), Bernoulli(0.5), linear truth, DM vs OLS_f over n x mean degree x sigma x gamma."""
    out, s = [], 1700
    for n in [1000, 5000, 20000]:
        for d in [10, 20, 40]:
            for sigma in [0.5, 1.0, 2.0]:
                for gamma in [0.0, 0.25, 0.5, 1.0, 2.0]:
                    s += 1
                    out.append(cell(f"sbm:{n},{n // 100},{d},0.8", "bern:0.5", dict(mech="shape", kind="linear", gamma=gamma, sigma=sigma),
                                    4, 100, f"n{n}|d{d}|s{sigma}", s, specs=["OLS_f", "ORACLE_D"], **FAST))
    return out


def e18_more_worlds():
    """experiment-repo#15(1). 20 worlds x 25 assignments per cell for the default scenario (Bernoulli(0.5), gamma = 2, linear and concave) on all six graphs,
    to see how the between-world standard error and the bias estimate behave with 4 versus 20 worlds."""
    out, s = [], 1800
    for gn, gs in ALL_G.items():
        for kind in ["linear", "concave"]:
            s += 1
            out.append(cell(gs, "bern:0.5", dict(mech="shape", kind=kind, gamma=2.0), 20, 25, gn, s, specs=["OLS_f", "OLS_zf", "ORACLE_D"], **FAST))
    return out


def e19_cluster_hajek():
    """experiment-repo#16(3). Design-based baselines paired with the cluster design on dense graphs: Hajek full exposure (unit and all neighbours treated vs
    all control, probability p^k with k clusters in the closed neighbourhood) and Hajek fractional exposure (kappa = 0.75, 0.9; cluster-design probabilities
    by convolution), Louvain clusters (resolution 1 and 5), SBM, ego-Facebook, Stanford3; linear and concave truth, gamma = 2."""
    out, s = [], 1900
    for gn in ["sbm", "ego", "stanford3"]:
        for res in [1.0, 5.0]:
            for kind in ["linear", "concave"]:
                s += 1
                out.append(cell(ALL_G[gn], f"louv:{res},0.5", dict(mech="shape", kind=kind, gamma=2.0), 4, 100, f"{gn}|res{res}", s,
                                specs=["OLS_f", "ORACLE_D"], hajek=True, no_acl=False, hac=False, kappas=(0.75, 0.9), extra=["HajekKappaCl"]))
    return out


def e20_factorial():
    """experiment-repo#14(2). Crossed design on SBM for the variance decomposition of log RMSE: n {1000, 5000, 20000} x mean degree {10, 20, 40} x
    p {0.1, 0.5} x sigma {0.5, 2} x graph-smooth baseline sd {0, 2} x spillover {linear, concave}; gamma = 2; 4 worlds x 100 assignments."""
    out, s = [], 2000
    for n in [1000, 5000, 20000]:
        for d in [10, 20, 40]:
            for p in [0.1, 0.5]:
                for sigma in [0.5, 2.0]:
                    for ag in [0.0, 2.0]:
                        for kind in ["linear", "concave"]:
                            s += 1
                            out.append(cell(f"sbm:{n},{n // 100},{d},0.8", f"bern:{p}", dict(mech="shape", kind=kind, gamma=2.0, sigma=sigma, alpha_graph=ag),
                                            4, 100, f"n{n}|d{d}|p{p}|s{sigma}|ag{ag}|{kind}", s, specs=["OLS_f", "ORACLE_D"], **FAST))
    return out


def e21_variance_components():
    """experiment-repo#10(a). Which part of the outcome's baseline moves the SD of OLS_f away from the independent-error variance law? Linear truth,
    gamma = 0, Bernoulli(0.5), six graphs; outcome variants: iid noise only (sigma = 1), + graph-smooth baseline (sd 1), + log-degree baseline (0.5),
    + iid baseline (sd 0.5); 4 worlds x 100 assignments."""
    out, s = [], 2200
    zero = dict(sigma=1.0, alpha_graph=0.0, alpha_deg=0.0, alpha_iid=0.0)
    variants = {"noise_only": zero, "graph_smooth": {**zero, "alpha_graph": 1.0}, "log_degree": {**zero, "alpha_deg": 0.5}, "iid_baseline": {**zero, "alpha_iid": 0.5}}
    for gn, gs in ALL_G.items():
        for vn, v in variants.items():
            s += 1
            out.append(cell(gs, "bern:0.5", dict(mech="shape", kind="linear", gamma=0.0, **v), 4, 100, f"{gn}|{vn}", s, specs=["OLS_f"], **FAST))
    return out


EXPERIMENTS = {f.__name__.split("_")[0]: f for f in [e1_interference_strength, e2_misspecification, e3_scaling,
                                                       e4_design, e5_noise_baseline, e6_inference,
                                                       e7_mechanisms, e8_noiseless_bias, e9_curvature, e10_bias_vs_n,
                                                       e11_gamma_misspecified, e12_hajek, e13_second_seed,
                                                       e14_matched_heavy_tail, e15_coverage, e16_estimator_scope, e17_crossover,
                                                       e18_more_worlds, e19_cluster_hajek, e20_factorial, e21_variance_components]}
