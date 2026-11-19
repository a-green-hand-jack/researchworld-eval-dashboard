"""Population (graph + outcome model), exposure features, designs, estimators."""
import numpy as np, scipy.sparse as sp
from sklearn.ensemble import HistGradientBoostingRegressor
from . import graphs as G

MECHS = ['linfrac', 'lincount', 'sat', 'quad', 'thresh', 'twohop', 'hetero', 'peer']


# ---------------------------------------------------------------- population
class Pop:
    """Fixed finite population: graph A (true interference graph), baseline a_i, mechanism.
    mu(z) is the noise-free expected outcome; tau = mean(mu(1)-mu(0)) is the GATE (exact)."""

    def __init__(self, graph_spec, mech, gamma=1.0, tau_d=1.0, seed=0, kappa=4.0, theta=0.7, steep=10.0, rho=0.5,
                 obs_noise_graph=0.0, A=None, comm_sd=0.5):
        self.spec, self.mech, self.gamma, self.tau_d = graph_spec, mech, gamma, tau_d
        self.kappa, self.theta, self.steep, self.rho = kappa, theta, steep, rho
        self.A = G.make_graph(graph_spec, seed) if A is None else A
        n = self.n = self.A.shape[0]
        self.deg = np.asarray(self.A.sum(1)).ravel()
        self.dbar = self.deg.mean()
        self.W = sp.diags(1.0 / self.deg) @ self.A
        self.W = self.W.tocsr()
        rng = np.random.default_rng([seed, 12345])
        ld = np.log(self.deg); self.logdeg = (ld - ld.mean()) / ld.std()
        base = G.clusters(graph_spec, self.A, 1.0, seed)
        b = rng.normal(size=base.max() + 1)
        self.a = 1 + 0.5 * self.logdeg + comm_sd * b[base] + 0.7 * rng.normal(size=n)
        u = 0.6 * self.logdeg + 0.8 * rng.normal(size=n)
        self.u = (u - u.mean()) / u.std()                      # latent slope heterogeneity
        # observed graph used by the analyst (possibly corrupted)
        if obs_noise_graph > 0:
            Ao = G.perturb(self.A, obs_noise_graph, np.random.default_rng([seed, 777]))
            dg = np.asarray(Ao.sum(1)).ravel(); dg[dg == 0] = 1
            self.Ao, self.dego = Ao, dg
            self.Wo = (sp.diags(1.0 / dg) @ Ao).tocsr()
            self.dbaro = dg.mean()
        else:
            self.Ao, self.dego, self.Wo, self.dbaro = self.A, self.deg, self.W, self.dbar
        self.tau = float(np.mean(self.mu(np.ones(n)) - self.mu(np.zeros(n))))

    # exposure maps on the TRUE graph
    def _g(self, z):
        m = self.mech; W = self.W
        x = W @ z
        if m == 'linfrac' or m == 'hetero': return x
        if m == 'lincount': return (self.A @ z) / self.dbar
        if m == 'sat': return (1 - np.exp(-self.kappa * x)) / (1 - np.exp(-self.kappa))
        if m == 'quad': return x ** 2
        if m == 'thresh':
            s = lambda t: 1 / (1 + np.exp(-self.steep * (t - self.theta)))
            return (s(x) - s(0.0)) / (s(1.0) - s(0.0))
        if m == 'twohop': return 0.5 * x + 0.5 * (W @ x)
        raise ValueError(m)

    def peer_S(self, v):
        s = v.copy(); t = v.copy()
        for _ in range(45):
            t = self.rho * (self.W @ t); s += t
        return s

    def mu(self, z):
        if self.mech == 'peer':
            return self.peer_S(self.a + self.tau_d * z)
        if self.mech == 'hetero':
            return self.a + self.tau_d * z + self.gamma * (1 + 0.5 * self.u) * self._g(z)
        return self.a + self.tau_d * z + self.gamma * self._g(z)

    # ---- analyst-side features (computed on OBSERVED graph) ----
    def xfrac(self, z): return self.Wo @ z
    def xcount(self, z): return (self.Ao @ z) / self.dbaro

    def feats(self, name, z):
        x = self.xfrac(z)
        ld = self.logdeg
        if name == 'x': return np.c_[z, x]
        if name == 'c': return np.c_[z, self.xcount(z)]
        if name == 'cd': return np.c_[z, self.xcount(z), ld]
        if name == 'xd': return np.c_[z, x, ld]
        if name == 'x2': return np.c_[z, x, self.Wo @ x, ld]
        if name == 'quad': return np.c_[z, x, x ** 2, z * x, ld]
        if name == 'rich': return np.c_[z, x, x ** 2, x ** 3, z * x, ld, z * ld, x * ld, self.Wo @ x]
        if name == 'gbdt': return np.c_[z, x, self.xcount(z), self.Wo @ x, ld]
        if name == 'oracle':
            m = self.mech
            if m == 'linfrac': return np.c_[z, x, ld]
            if m == 'lincount': return np.c_[z, self.xcount(z), ld]
            if m in ('sat', 'quad', 'thresh'):
                if m == 'quad': g = x ** 2
                elif m == 'sat': g = (1 - np.exp(-self.kappa * x)) / (1 - np.exp(-self.kappa))
                else:
                    s = lambda t: 1 / (1 + np.exp(-self.steep * (t - self.theta)))
                    g = (s(x) - s(0.0)) / (s(1.0) - s(0.0))
                return np.c_[z, g, ld]
            if m == 'twohop': return np.c_[z, x, self.Wo @ x, ld]
            if m == 'hetero': return np.c_[z, x, x * self.u, ld]
            if m == 'peer': return np.c_[self.peer_S(z), ld]
        raise ValueError(name)


# ---------------------------------------------------------------- designs
class Design:
    def __init__(self, kind, p=0.5, labels=None, levels=(0.1, 0.3, 0.5, 0.7, 0.9)):
        self.kind, self.p, self.labels, self.levels = kind, p, labels, np.asarray(levels)
        if labels is not None: self.K = labels.max() + 1

    def draw(self, n, rng):
        k = self.kind
        if k == 'bern': return (rng.random(n) < self.p).astype(float)
        if k == 'cluster':     # cluster-level complete randomization with ~p share of clusters treated
            t = np.zeros(self.K); t[rng.choice(self.K, int(round(self.p * self.K)), replace=False)] = 1
            return t[self.labels]
        if k == 'sat':         # randomized saturation: cluster picks p_c, units Bernoulli(p_c)
            pc = rng.choice(self.levels, self.K)
            return (rng.random(n) < pc[self.labels]).astype(float)
        raise ValueError(k)


# ---------------------------------------------------------------- estimators
def ols_estimate(Phi1, Phi0, Phiz, y, ridge=1e-8, want_w=False, labels=None, infer=False):
    n = len(y)
    X = np.c_[np.ones(n), Phiz]
    c = np.r_[0.0, (Phi1 - Phi0).mean(0)]
    XtX = X.T @ X + ridge * np.eye(X.shape[1]) * n
    inv = np.linalg.inv(XtX)
    beta = inv @ (X.T @ y)
    tau = float(c @ beta)
    out = {'tau': tau}
    if want_w or infer:
        w = X @ (inv @ c)
        out['w2'] = float(np.sqrt(c @ inv @ c)); out['w1'] = float(np.abs(w).sum())
        out['wneg'] = float(np.minimum(w, 0).sum() * -1)
        if infer:
            e = y - X @ beta
            h = np.einsum('ij,jk,ik->i', X, inv, X)
            out['se_hc0'] = float(np.sqrt(np.sum((w * e) ** 2)))
            out['se_hc3'] = float(np.sqrt(np.sum((w * e / (1 - h)) ** 2)))
            if labels is not None:
                s = np.bincount(labels, weights=w * e)
                out['se_cl'] = float(np.sqrt(np.sum(s ** 2)))
            out['se_iid'] = float(np.sqrt(np.sum(e ** 2) / (n - X.shape[1]) * (c @ inv @ c)))
    return out


OLS_SETS = ['x', 'c', 'cd', 'xd', 'x2', 'quad', 'rich', 'oracle']
ALL_EST = ['DM'] + ['OLS-' + s for s in OLS_SETS] + ['GBDT', 'Hajek']


class Estimators:
    """Pre-computes target features (all-treated / all-control) once per population."""

    def __init__(self, pop, design, hajek_q=0.75, hajek_M=400, rng=None, which=None, infer_labels=None, do_infer=False):
        self.pop, self.design = pop, design
        n = pop.n
        self.one, self.zero = np.ones(n), np.zeros(n)
        self.which = which or ALL_EST
        self.T = {s: (pop.feats(s, self.one), pop.feats(s, self.zero)) for s in OLS_SETS}
        self.Tg = (pop.feats('gbdt', self.one), pop.feats('gbdt', self.zero))
        self.do_infer, self.infer_labels = do_infer, infer_labels
        self.q = hajek_q
        if 'Hajek' in self.which:
            rng = rng or np.random.default_rng(0)
            p1 = np.zeros(n); p0 = np.zeros(n)
            for _ in range(hajek_M):
                z = design.draw(n, rng); x = pop.xfrac(z)
                p1 += (z == 1) & (x >= hajek_q); p0 += (z == 0) & (x <= 1 - hajek_q)
            self.pi1 = np.maximum(p1, 1) / (hajek_M + 1); self.pi0 = np.maximum(p0, 1) / (hajek_M + 1)

    def run(self, z, y, rng_seed=0):
        pop = self.pop; out = {}
        if 'DM' in self.which:
            t1, t0 = z == 1, z == 0
            out['DM'] = {'tau': float(y[t1].mean() - y[t0].mean()) if t1.any() and t0.any() else np.nan}
        for s in OLS_SETS:
            if 'OLS-' + s in self.which:
                out['OLS-' + s] = ols_estimate(self.T[s][0], self.T[s][1], pop.feats(s, z), y, want_w=True,
                                              labels=self.infer_labels, infer=(self.do_infer and s == 'x'))
        if 'GBDT' in self.which:
            F = pop.feats('gbdt', z)
            m = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.1, max_depth=4, min_samples_leaf=20,
                                              random_state=rng_seed).fit(F, y)
            out['GBDT'] = {'tau': float(np.mean(m.predict(self.Tg[0]) - m.predict(self.Tg[1])))}
        if 'Hajek' in self.which:
            x = pop.xfrac(z)
            e1 = (z == 1) & (x >= self.q); e0 = (z == 0) & (x <= 1 - self.q)
            if e1.any() and e0.any():
                w1 = 1 / self.pi1[e1]; w0 = 1 / self.pi0[e0]
                out['Hajek'] = {'tau': float((w1 * y[e1]).sum() / w1.sum() - (w0 * y[e0]).sum() / w0.sum()),
                                'n1': int(e1.sum()), 'n0': int(e0.sum())}
            else:
                out['Hajek'] = {'tau': np.nan, 'n1': int(e1.sum()), 'n0': int(e0.sum())}
        return out
