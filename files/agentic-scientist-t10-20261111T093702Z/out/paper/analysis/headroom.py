"""Population-level headroom (oracle ceiling) for control-variate mean intervals on the final pools.

For features f(Yhat) in the span of {Yhat, E[Y|Yhat]} the optimally weighted control-variate
estimator has n*Var = Var(Y) * (1 - eta2 / (1 + n/N)), while the PPI++ estimator (scalar weight on
Yhat only, clipped to [0,1]) has n*Var = Var(Y) - 2 lam Cov + lam^2 (1+n/N) Var(Yhat).
Widths scale with sqrt(Var). This script evaluates those formulas on the evaluator's final pools
(read-only) and on the evaluator's known-truth synthetic regimes, then compares with observed
sealed-final width ratios read from paper_data.json.

Inputs : ./task/resources/final/*.npz, ./task/evaluate_final.py (protocol constants, copied below),
         ./paper_data.json (observed final metrics)
Output : ./analysis/headroom_derived.json
"""
import json, math
from pathlib import Path
import numpy as np
from sklearn.isotonic import IsotonicRegression

ROOT = Path(__file__).resolve().parent.parent
# @evidence[[source_evidence/evaluate_final.py#POOLS]]
POOLS = {"census_income": ("census_income.npz", "Y", "Yhat"),
         "census_healthcare": ("census_healthcare.npz", "Y", "Yhat"),
         "census_education": ("census_education.npz", "Y", "Yhat"),
         "plankton": ("plankton.npz", "Y_unlabeled", "Yhat_unlabeled")}
N_LAB, N_UNL = 500, 20000
# @evidence[[source_evidence/evaluate_final.py#SYNTH_REGIMES]]
REGIMES = [("linear_calibrated", dict(a=-0.5, b=1.2, s=0.8, kind="linear", noise_hat=0.5)),
           ("nonlinear_miscalibrated", dict(a=3.0, b=1.0, s=0.6, kind="cubic", noise_hat=0.1)),
           ("uninformative", dict(a=2.0, b=1.0, s=1.2, kind="independent", noise_hat=1.0)),
           ("heteroscedastic", dict(a=0.0, b=2.0, s=0.8, kind="hetero", rate=0.5, noise_hat=0.4))]
SYNTH_N, SYNTH_BIG_N = [200, 500], [2000, 20000]


def synth(spec, m, rng):
    z, eps, eta = rng.standard_normal((3, m))
    k = spec["kind"]
    if k == "hetero":
        y = spec["a"] + spec["b"] * z + np.exp(spec["rate"] * z) * eps * spec["s"]
        yh = spec["a"] + spec["b"] * z + spec["noise_hat"] * eta
    elif k == "cubic":
        y = spec["a"] + spec["b"] * z + spec["s"] * eps
        yh = 0.5 * z ** 3 + 0.2 * z + spec["noise_hat"] * eta
    elif k == "independent":
        y = spec["a"] + spec["b"] * z + spec["s"] * eps
        yh = spec["a"] + spec["b"] * eta
    else:
        y = spec["a"] + spec["b"] * z + spec["s"] * eps
        yh = spec["a"] + spec["b"] * z + spec["noise_hat"] * eta
    return y, yh


def moments(y, yh):
    vy, vh = y.var(), yh.var()
    cov = float(np.mean((y - y.mean()) * (yh - yh.mean())))
    iso = IsotonicRegression(increasing=cov >= 0, out_of_bounds="clip")
    fit = iso.fit(yh, y).predict(yh)
    eta2_iso = float(np.var(fit) / vy)
    # quantile-bin conditional mean (200 bins) as a second estimate of the correlation ratio
    edges = np.unique(np.quantile(yh, np.linspace(0, 1, 201)[1:-1]))
    idx = np.searchsorted(edges, yh, side="right")
    cnt = np.bincount(idx); sm = np.bincount(idx, weights=y)
    cm = (sm / np.maximum(cnt, 1))[idx]
    eta2_bin = float(np.var(cm) / vy)
    return dict(var_y=float(vy), var_yhat=float(vh), cov=cov, rho2=cov ** 2 / (vy * vh),
                eta2_iso=eta2_iso, eta2_bin=eta2_bin)


def var_ppi(mo, n, big_n, lam):
    r = n / big_n
    return mo["var_y"] - 2 * lam * mo["cov"] + lam ** 2 * (1 + r) * mo["var_yhat"], r


def widths(mo, n, big_n, eta2):
    """n*Var for classical, PPI(lam=1), PPI++, and oracle-recalibrated control variate."""
    r = n / big_n
    lam = min(1.0, max(0.0, mo["cov"] / ((1 + r) * mo["var_yhat"])))
    v = dict(classical=mo["var_y"],
             ppi_lam1=var_ppi(mo, n, big_n, 1.0)[0],
             ppi_pp=var_ppi(mo, n, big_n, lam)[0],
             oracle_linear=mo["var_y"] * (1 - mo["rho2"] / (1 + r)),   # unclipped linear weight on Yhat
             oracle_recal=mo["var_y"] * (1 - eta2 / (1 + r)))
    # n*Var -> SE = sqrt(n*Var / n); the common 2*z/sqrt(n) factor cancels in ratios but we keep n
    return {k: math.sqrt(x / n) for k, x in v.items()}, lam


def s(num, den):
    return -math.log(num / den)


def family_ratios(episodes):
    """episodes: list of (moments, n, N, eta2). Ratio-of-sums of widths, as in the evaluator."""
    tot = dict(classical=0.0, ppi_lam1=0.0, ppi_pp=0.0, oracle_linear=0.0, oracle_recal=0.0)
    for mo, n, big_n, eta2 in episodes:
        w, _ = widths(mo, n, big_n, eta2)
        for k in tot:
            tot[k] += w[k]
    return dict(oracle_vs_ppi_pp=s(tot["oracle_recal"], tot["ppi_pp"]),
                oracle_linear_vs_ppi_pp=s(tot["oracle_linear"], tot["ppi_pp"]),
                oracle_vs_ppi_lam1=s(tot["oracle_recal"], tot["ppi_lam1"]),
                oracle_vs_classical=s(tot["oracle_recal"], tot["classical"]),
                ppi_pp_vs_classical=s(tot["ppi_pp"], tot["classical"]),
                ppi_pp_vs_ppi_lam1=s(tot["ppi_pp"], tot["ppi_lam1"]))


def main():
    out = {"real": {}, "synthetic": {}}
    fam = {}
    for name, (fn, yk, hk) in POOLS.items():
        with np.load(ROOT / "task/resources/final" / fn, allow_pickle=False) as d:
            y = np.asarray(d[yk], dtype=float); yh = np.asarray(d[hk], dtype=float)
        mo = moments(y, yh)
        mo["pool_size"] = int(y.size)
        mo["n_unique_yhat"] = int(np.unique(yh).size)
        _, lam = widths(mo, N_LAB, N_UNL, mo["eta2_iso"])
        mo["lambda_star_ppi_pp"] = lam
        mo["lambda_unclipped"] = mo["cov"] / ((1 + N_LAB / N_UNL) * mo["var_yhat"])
        # eta2 used in the ceiling: the larger of the two estimates is not used; use isotonic
        # (monotone class, what the evaluated method fits) and report the bin version alongside.
        mo.update(family_ratios([(mo, N_LAB, N_UNL, max(mo["eta2_iso"], mo["rho2"]))]))
        out["real"][name] = mo
        fam[name] = mo
    rng = np.random.default_rng(20261111)
    reg_mo = {}
    for name, spec in REGIMES:
        y, yh = synth(spec, 2_000_000, rng)
        mo = moments(y, yh)
        mo["eta2_used"] = max(mo["eta2_iso"], mo["rho2"])
        reg_mo[name] = mo
    out["synthetic_regimes"] = reg_mo
    eps = []
    for j in range(100):   # evaluator plan: regime j%4, n by (j//4)%2, N by (j//8)%2
        name = REGIMES[j % 4][0]
        mo = reg_mo[name]
        eps.append((mo, SYNTH_N[(j // 4) % 2], SYNTH_BIG_N[(j // 8) % 2], mo["eta2_used"]))
    out["synthetic"] = family_ratios(eps)
    fam["synthetic"] = out["synthetic"]
    # observed sealed-final values
    pd_ = json.load(open(ROOT / "paper_data.json"))
    m = pd_["final_evaluation"]["metrics"]   # @evidence[[paper_data.json#final_evaluation.metrics]]
    fams = ["census_income", "census_healthcare", "census_education", "plankton", "synthetic"]
    out["observed_vs_ppi_pp"] = {f: m[f"log_ratio_vs_ppi_family_{f}"] for f in fams}
    out["oracle_vs_ppi_pp"] = {f: fam[f]["oracle_vs_ppi_pp"] for f in fams}
    out["oracle_linear_vs_ppi_pp"] = {f: fam[f]["oracle_linear_vs_ppi_pp"] for f in fams}
    out["oracle_linear_aggregate_vs_ppi_pp"] = float(np.mean(list(out["oracle_linear_vs_ppi_pp"].values())))
    out["oracle_aggregate_vs_ppi_pp"] = float(np.mean([out["oracle_vs_ppi_pp"][f] for f in fams]))
    out["oracle_aggregate_vs_ppi_lam1"] = float(np.mean([fam[f]["oracle_vs_ppi_lam1"] for f in fams]))
    out["oracle_aggregate_vs_classical"] = float(np.mean([fam[f]["oracle_vs_classical"] for f in fams]))
    out["ppi_pp_aggregate_vs_classical"] = float(np.mean([fam[f]["ppi_pp_vs_classical"] for f in fams]))
    out["ppi_pp_aggregate_vs_ppi_lam1"] = float(np.mean([fam[f]["ppi_pp_vs_ppi_lam1"] for f in fams]))
    out["observed_aggregate"] = {"vs_ppi_pp": m["combined_score"],
                                 "vs_ppi_lam1": m["log_ratio_vs_ppi_lambda1_mean"],
                                 "vs_classical": m["log_ratio_vs_classical_mean"]}
    # coverage arithmetic (exact binomial tails under the nominal level)
    from scipy.stats import binom
    n_pool, k_pool = 500, round(m["coverage_pooled"] * 500)
    n_min, k_min = 100, round(m["coverage_min_family"] * 100)
    out["coverage"] = {
        "pooled_covered": k_pool, "pooled_n": n_pool,
        "pooled_binom_lower_tail_p": float(binom.cdf(k_pool, n_pool, 0.95)),
        "pooled_mc_se": math.sqrt(m["coverage_pooled"] * (1 - m["coverage_pooled"]) / n_pool),
        "min_family_covered": k_min, "min_family_n": n_min,
        "min_family_binom_lower_tail_p": float(binom.cdf(k_min, n_min, 0.95)),
        "min_family_mc_se": math.sqrt(m["coverage_min_family"] * (1 - m["coverage_min_family"]) / n_min)}
    # derived width reductions 1 - exp(-s)
    out["derived_width_reduction_vs_ppi_pp"] = {f: 1 - math.exp(-out["observed_vs_ppi_pp"][f]) for f in fams}
    out["derived_width_reduction_aggregate"] = {k: 1 - math.exp(-v) for k, v in out["observed_aggregate"].items()}
    out["partition_scores"] = [e["score"] for e in pd_["final_evaluation"]["evaluation_evidence"]["episodes"]]
    # sensitivity of the oracle recalibration gain over an unclipped linear weight to r = n/N (Eq. ceiling)
    sens = {}
    cells = [("n200_N20000", 200, 20000), ("n500_N20000", 500, 20000), ("n200_N2000", 200, 2000), ("n500_N2000", 500, 2000)]
    srcs = {"synthetic_nonlinear_miscalibrated": (reg_mo["nonlinear_miscalibrated"]["rho2"], reg_mo["nonlinear_miscalibrated"]["eta2_used"]),
            "census_income": (fam["census_income"]["rho2"], max(fam["census_income"]["eta2_iso"], fam["census_income"]["rho2"]))}
    for nm, (rho2, eta2) in srcs.items():
        sens[nm] = {c: {"r": n / big, "log_ratio": -0.5 * math.log((1 - eta2 / (1 + n / big)) / (1 - rho2 / (1 + n / big)))}
                    for c, n, big in cells}
    out["oracle_recal_over_linear_by_cell"] = sens
    # composition of the five reset-seed partitions, replicating make_plan() in task/evaluate_final.py
    # @evidence[[source_evidence/evaluate_final.py#make_plan]]
    seeds = [9101, 9102, 9103, 9104, 9105]
    plan = []
    for j in range(100):
        for f in fams:
            plan.append((f, "main"))
        if j < 30:
            for b in ["census_income", "plankton"]:
                for k in ("const", "perm", "shift"):
                    plan.append((b, k))
    comp = {str(sd): {f: 0 for f in fams} for sd in seeds}
    for i, (f, k) in enumerate(plan):
        if k == "main":
            comp[str(seeds[i % 5])][f] += 1
    out["partition_composition_main_episodes"] = comp
    json.dump(out, open(ROOT / "analysis/headroom_derived.json", "w"), indent=1)
    print(json.dumps({k: out[k] for k in ["oracle_vs_ppi_pp", "oracle_linear_vs_ppi_pp", "oracle_linear_aggregate_vs_ppi_pp", "observed_vs_ppi_pp", "oracle_aggregate_vs_ppi_pp",
          "oracle_aggregate_vs_ppi_lam1", "oracle_aggregate_vs_classical", "ppi_pp_aggregate_vs_classical",
          "observed_aggregate", "coverage", "derived_width_reduction_vs_ppi_pp", "derived_width_reduction_aggregate"]}, indent=1))
    for f, mo in out["real"].items():
        print(f, {k: round(v, 4) if isinstance(v, float) else v for k, v in mo.items()})
    for f, mo in reg_mo.items():
        print(f, {k: round(v, 4) for k, v in mo.items()})

main()
