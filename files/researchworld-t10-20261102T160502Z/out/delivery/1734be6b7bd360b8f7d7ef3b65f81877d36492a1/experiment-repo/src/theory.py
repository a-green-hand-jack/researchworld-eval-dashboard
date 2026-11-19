"""Q1: population-level variance floors and predicted width ratios, per dataset (pool = population).

For labeled n, unlabeled N, omega = N/(n+N); class theta_phi = mean_lab(Y-phi(f)) + mean_unl phi(f):
    n*V(phi)       = Var(Y-phi) + (n/N) Var(phi)
    PPI (phi=f)    : Var(Y-f) + (n/N) Var f
    M3 (phi=lam f, lam=min(1, lam*), lam*=Cov(Y,f)/((1+n/N) Var f))   [ppi_py clips lambda to [0,1]]
    unclipped PPI++: sigma^2 (1 - omega rho^2)
    floor (phi = omega*E[Y|f])   : sigma^2 (1 - omega R2cal),  R2cal = Var E[Y|f]/sigma^2  (derivation: theory.md)
R2cal is estimated by K-fold cross-fitted calibrators (an in-sample nonparametric g would give a spurious floor):
   R2cal_hat = 1 - mean((Y - g_oof(f))^2)/Var(Y)   (conservative: estimation error lowers it).
Predicted asymptotic width ratio M4/M3 = sqrt(V_floor / V_M3) (no cost for learning g).
"""
import numpy as np, pandas as pd, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import data as D
import estimators as E
import grids


def oof_r2(Y, f, kind, K=5, seed=0):
    rng = np.random.default_rng(seed)
    fold = rng.permutation(len(Y)) % K
    g = np.empty(len(Y))
    for k in range(K):
        tr = fold != k
        g[~tr] = E.CAL[kind](f[tr], Y[tr])(f[~tr])
    return 1 - np.mean((Y - g) ** 2) / Y.var()


def v_pred(s2, rho2, r2, Cov, v, n, N):
    om = N / (n + N)
    lam_star = Cov / ((1 + n / N) * v)
    lam = min(1.0, max(0.0, lam_star))
    V_m3 = (s2 - 2 * lam * Cov + lam ** 2 * v) / n + lam ** 2 * v / N
    return dict(V_classical=s2 / n, V_ppi=(s2 - 2 * Cov + v) / n + v / N, V_M3=V_m3, V_nc=s2 * (1 - om * rho2) / n,
                V_floor=s2 * (1 - om * r2) / n, lam_star=lam_star)


def main():
    pops, rows = {}, []
    for name in D.DATASETS:
        p = D.population(name); Y, f = p["Y"], p["f"]
        s2, v, Cov = Y.var(), f.var(), np.cov(Y, f, bias=True)[0, 1]
        rho2 = Cov ** 2 / (s2 * v)
        r2 = {k: oof_r2(Y, f, k) for k in ["iso", "bin", "spl"]}
        pops[name] = dict(size=len(Y), sigma2=s2, var_f=v, cov_yf=Cov, rho2=rho2, lam_star_inf=Cov / v,
                          slope_gt1=bool(Cov / v > 1), **{"r2cal_" + k: x for k, x in r2.items()})
    pd.DataFrame(pops).T.rename_axis("dataset").reset_index().to_csv("results/theory_population.csv", index=False)
    cells = set((d, n, N) for g in ["real_primary", "real_appendix", "real_nsweep", "shift"] for (d, n, N, R, fl) in grids.GRIDS[g](1))
    for d, n, N in sorted(cells):
        q = pops[d]
        for k in ["iso", "bin", "spl"]:
            V = v_pred(q["sigma2"], q["rho2"], q["r2cal_" + k], q["cov_yf"], q["var_f"], n, N)
            rows.append(dict(dataset=d, n=n, N=N, calibrator=k, omega=N / (n + N), pred_ratio_M4_vs_M3=np.sqrt(V["V_floor"] / V["V_M3"]),
                             pred_ratio_M4_vs_nc=np.sqrt(V["V_floor"] / V["V_nc"]), pred_ratio_M3_vs_classical=np.sqrt(V["V_M3"] / V["V_classical"]),
                             pred_ratio_ppi_vs_M3=np.sqrt(V["V_ppi"] / V["V_M3"]), lam_star=V["lam_star"]))
    out = pd.DataFrame(rows); out.to_csv("results/theory_predicted_ratios.csv", index=False)
    pd.set_option("display.width", 250)
    print(pd.DataFrame(pops).T.round(4).to_string())
    print(out[(out.N == 20 * out.n) & (out.n == 400)].round(4).to_string())


if __name__ == "__main__":
    main()
