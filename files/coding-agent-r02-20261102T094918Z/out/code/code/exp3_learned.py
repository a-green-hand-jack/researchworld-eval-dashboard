"""E3: learned predictor (MLP trained with soft cross-entropy), optional heteroscedastic noise, and adaptive methods:
split / Studentised (normalised) / Mondrian-by-predicted-scale / Mondrian-by-confidence.  Writes results/e3_learned.csv"""
import sys, time
import numpy as np, pandas as pd
import torch
from sklearn.ensemble import GradientBoostingRegressor
from joblib import Parallel, delayed
from ccp.geometry import SCORES, clr
from ccp.synth import SynthProblem
from ccp.conformal import conformal_quantile
from ccp.evalkit import SliceCoverage, MassLookup, quantile_bins

ALPHA, N_CAL, N_SCALE, M_TEST, N_CENT, NB = 0.1, 1000, 2000, 40000, 150, 10
R = 10 if "--quick" in sys.argv else 100
USE = {"chi2": SCORES["chi2"], "euclid": SCORES["euclid"], "aitchison": SCORES["aitchison"]}


def fit_mlp(X, Y, seed, epochs=400):
    torch.manual_seed(seed)
    Xt, Yt = torch.tensor(X, dtype=torch.float32), torch.tensor(Y, dtype=torch.float32)
    net = torch.nn.Sequential(torch.nn.Linear(X.shape[1], 64), torch.nn.Tanh(), torch.nn.Linear(64, 64), torch.nn.Tanh(),
                              torch.nn.Linear(64, Y.shape[1]))
    opt = torch.optim.Adam(net.parameters(), lr=5e-3, weight_decay=1e-4)
    n = len(X)
    for ep in range(epochs):
        perm = torch.randperm(n)
        for i in range(0, n, 256):
            idx = perm[i:i + 256]
            loss = -(Yt[idx] * torch.log_softmax(net(Xt[idx]), -1)).sum(-1).mean()
            opt.zero_grad(); loss.backward(); opt.step()
    net.eval()
    def f(Xn):
        with torch.no_grad():
            return torch.softmax(net(torch.tensor(Xn, dtype=torch.float32)), -1).numpy().astype(np.float64)
    return f


def run(fam, het, n_train, ps):
    torch.set_num_threads(1)
    D = 5
    pr = SynthProblem(D=D, family=fam, kappa=100, tau=1.5, seed=ps, het=het)
    rng = np.random.default_rng(31 * ps + 5)
    Xa, _, Ya = pr.sample(n_train, rng)
    f = fit_mlp(Xa, Ya, ps)
    # scale models (trained on separate data) -- one per score
    Xs, _, Ys = pr.sample(N_SCALE, rng)
    Ps = f(Xs)
    feat = lambda X, P: np.hstack([X, clr(P)])
    scale_models = {}
    for n, fn in USE.items():
        g = GradientBoostingRegressor(n_estimators=150, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=ps)
        g.fit(feat(Xs, Ps), np.log(fn(Ys, Ps) + 1e-12))
        scale_models[n] = g
    Xt, mu_t, y_t = pr.sample(M_TEST, rng)
    Pt = f(Xt)
    true_scale = pr.noise_scale(Xt)
    sig = {n: np.exp(scale_models[n].predict(feat(Xt, Pt))) for n in USE}
    b_het, _ = quantile_bins(true_scale, NB)
    conf = Pt.max(-1)
    b_conf, e_conf = quantile_bins(conf, NB)
    cidx = rng.choice(M_TEST, N_CENT, replace=False)
    ml = MassLookup(Pt[cidx], USE, a=1.0, seed=ps)
    # predictor quality: mean KL(mu || f) for reference
    kl_pred = float((mu_t * (np.log(mu_t) - np.log(np.maximum(Pt, 1e-12)))).sum(-1).mean())
    St = {n: fn(y_t, Pt) for n, fn in USE.items()}
    rows = []
    for r in range(R):
        rr = np.random.default_rng([ps, r, 3])
        Xc, _, yc = pr.sample(N_CAL, rr)
        Pc = f(Xc)
        sig_c = {n: np.exp(scale_models[n].predict(feat(Xc, Pc))) for n in USE}
        bconf_c, _ = quantile_bins(Pc.max(-1), NB, edges=e_conf)
        for n, fn in USE.items():
            sc = fn(yc, Pc)
            # scale-bin edges from the test-pool distribution of predicted scale (a held-out sample) -- fixed across reps
            sb_edges = np.quantile(sig[n], np.linspace(0, 1, NB + 1)[1:-1])
            bs_c = np.searchsorted(sb_edges, sig_c[n], side="right")
            bs_t = np.searchsorted(sb_edges, sig[n], side="right")
            thr = {}
            thr["split"] = np.full(M_TEST, conformal_quantile(sc, ALPHA))
            thr["studentised"] = conformal_quantile(sc / sig_c[n], ALPHA) * sig[n]
            qs = np.array([conformal_quantile(sc[bs_c == b], ALPHA) for b in range(NB)])
            thr["mondrian_scale"] = qs[bs_t]
            qc = np.array([conformal_quantile(sc[bconf_c == b], ALPHA) for b in range(NB)])
            thr["mondrian_conf"] = qc[b_conf]
            for meth, q in thr.items():
                cov = St[n] <= q
                ch = np.array([cov[b_het == b].mean() if (b_het == b).any() else np.nan for b in range(NB)])
                cc = np.array([cov[b_conf == b].mean() for b in range(NB)])
                lm = np.log(np.maximum([ml.mass(n, i, q[cidx[i]]) for i in range(N_CENT)], 1e-300)).mean()
                rows.append(dict(family=fam, het=het, n_train=n_train, prob=ps, rep=r, score=n, method=meth, cov=cov.mean(),
                                 worst_het=np.nanmax(np.abs(ch - 0.9)) if np.isfinite(ch).any() else np.nan, worst_conf=np.abs(cc - 0.9).max(), lm1=lm, kl_pred=kl_pred))
    return rows


if __name__ == "__main__":
    t0 = time.time()
    tasks = [(f, h, nt, s) for f in ("dirichlet", "logistic_normal") for h in (0.0, 1.0) for nt in (300, 3000) for s in range(5)]
    out = Parallel(n_jobs=10)(delayed(run)(*t) for t in tasks)
    df = pd.DataFrame([r for rows in out for r in rows])
    df.to_csv("/work/results/e3_learned%s.csv" % ("_quick" if "--quick" in sys.argv else ""), index=False)
    print("done", time.time() - t0)
