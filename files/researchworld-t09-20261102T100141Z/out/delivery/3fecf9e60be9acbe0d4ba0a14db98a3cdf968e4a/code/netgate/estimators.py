"""GATE estimators. Each takes a `Sim` context and returns (estimate, se or nan)."""
import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import HistGradientBoostingRegressor


def features(net, z, name):
    """Feature matrix as a function of the assignment vector z (used at observed z, z=1, z=0)."""
    W = net.W
    f = W @ z
    cols = [z]
    if name == "ols_z":
        pass
    elif name == "ols_f":
        cols.append(f)
    elif name == "ols_cnt":
        cols.append((net.A @ z) / net.deg.mean())
    elif name == "ols_cnt_adj":   # count + degree control (fixes degree confounding of the count feature)
        cols += [(net.A @ z) / net.deg.mean(), net.zl]
    elif name == "ols_f2":
        cols += [f, W @ f]
    elif name == "ols_poly":
        cols += [f, f**2, z * f]
    elif name == "ols_poly3":
        cols += [f, f**2, f**3, z * f]
    elif name == "ols_f_adj":
        cols += [f, net.zl, net.zc]
    elif name == "ols_f_deg":
        cols += [f, net.zl, f * net.zl, z * net.zl]
    elif name == "ols_f_both":     # fraction and count together
        cols += [f, (net.A @ z) / net.deg.mean()]
    elif name == "ridge_rich":
        f2 = W @ f
        cols += [f, f2, f**2, z * f, net.zl, f * net.zl, z * net.zl, net.zc, (net.A @ z) / net.deg.mean()]
    elif name == "gbm":
        f2 = W @ f
        cols += [f, f2, net.zl, net.zc]
    else:
        raise ValueError(name)
    return np.column_stack(cols)


def prep(net):
    ld = np.log(net.deg)
    net.zl = (ld - ld.mean()) / (ld.std() + 1e-12)
    cc = net.clustering()
    net.zc = (cc - cc.mean()) / (cc.std() + 1e-12)


def _fit_predict(name, X, y, X1, X0):
    if name.startswith("ols"):
        Xd = np.column_stack([np.ones(len(y)), X])
        beta, *_ = np.linalg.lstsq(Xd, y, rcond=None)
        m = (np.column_stack([np.ones(len(y)), X1]) - np.column_stack([np.ones(len(y)), X0])).mean(0)
        return float(m @ beta), (Xd, beta, m)
    if name == "ridge_rich":
        mu, sd = X.mean(0), X.std(0) + 1e-12
        mdl = RidgeCV(alphas=np.logspace(-3, 3, 13)).fit((X - mu) / sd, y)
        return float((mdl.predict((X1 - mu) / sd) - mdl.predict((X0 - mu) / sd)).mean()), None
    if name == "gbm":
        mdl = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.1, max_leaf_nodes=15,
                                            random_state=0).fit(X, y)
        return float((mdl.predict(X1) - mdl.predict(X0)).mean()), None
    raise ValueError(name)


def regression_gate(net, z, y, name, labels=None, want_se=False):
    n = net.n
    X = features(net, z, name)
    X1 = features(net, np.ones(n), name)
    X0 = features(net, np.zeros(n), name)
    est, aux = _fit_predict(name, X, y, X1, X0)
    se = np.nan
    if want_se and aux is not None:
        Xd, beta, m = aux
        r = y - Xd @ beta
        bread = np.linalg.inv(Xd.T @ Xd)
        sc = Xd * r[:, None]
        if labels is None:
            meat = sc.T @ sc
        else:   # cluster-robust sandwich over graph communities
            k = labels.max() + 1
            S = np.zeros((k, Xd.shape[1]))
            np.add.at(S, labels, sc)
            meat = S.T @ S
        V = bread @ meat @ bread
        se = float(np.sqrt(max(m @ V @ m, 0)))
    return est, se


def diff_in_means(z, y):
    return float(y[z == 1].mean() - y[z == 0].mean())


def hajek_exposure(net, design, z, y):
    """Hajek (self-normalised HT) contrast of fully-treated vs fully-control closed neighbourhoods."""
    f = net.W @ z
    t_ex = (z == 1) & (f == 1)
    c_ex = (z == 0) & (f == 0)
    if t_ex.sum() == 0 or c_ex.sum() == 0:
        return np.nan
    wt = 1 / design.prob_full(True)[t_ex]
    wc = 1 / design.prob_full(False)[c_ex]
    return float((wt * y[t_ex]).sum() / wt.sum() - (wc * y[c_ex]).sum() / wc.sum())


def hajek_q(net, design, z, y, q=0.75):
    """Hajek q-threshold neighbourhood-treatment-response estimator (Bernoulli design only):
    treated units with >= q of neighbours treated vs control units with >= q of neighbours control."""
    if design.kind != "bernoulli":
        return np.nan
    from scipy.stats import binom
    p, d = design.p, net.deg.astype(int)
    f = net.W @ z
    t_ex = (z == 1) & (f >= q - 1e-12)
    c_ex = (z == 0) & (f <= 1 - q + 1e-12)
    if t_ex.sum() == 0 or c_ex.sum() == 0:
        return np.nan
    kt = np.ceil(q * d - 1e-9)                     # need >= kt treated neighbours
    pt = p * binom.sf(kt - 1, d, p)
    kc = np.floor((1 - q) * d + 1e-9)              # need <= kc treated neighbours
    pc = (1 - p) * binom.cdf(kc, d, p)
    wt, wc = 1 / pt[t_ex], 1 / pc[c_ex]
    return float((wt * y[t_ex]).sum() / wt.sum() - (wc * y[c_ex]).sum() / wc.sum())
