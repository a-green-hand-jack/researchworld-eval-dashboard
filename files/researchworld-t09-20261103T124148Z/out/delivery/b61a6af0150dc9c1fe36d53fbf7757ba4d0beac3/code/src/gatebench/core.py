"""Fixed-graph GATE simulation and exact linear-smoother diagnostics.

The simulation averages over treatment assignment and fresh mean-zero noise.
The same additive noise would appear in both potential outcomes, so it cancels
from each realization's GATE. Conditional means and variances below condition
on the realized assignment, graph and node covariates.
"""
from dataclasses import dataclass
from functools import cached_property
import numpy as np
from scipy import sparse
from scipy.special import expit
from sklearn.preprocessing import SplineTransformer


@dataclass
class Graph:
    name: str
    adjacency: sparse.csr_matrix
    x: np.ndarray
    clusters: np.ndarray

    @property
    def n(self):
        return self.adjacency.shape[0]

    @cached_property
    def degree(self):
        return np.asarray(self.adjacency.sum(axis=1)).ravel()

    @cached_property
    def transition(self):
        d = self.degree
        # Isolates use own treatment as exposure, keeping all-one exposure one.
        return sparse.diags(1 / np.maximum(d, 1)) @ self.adjacency + sparse.diags((d == 0).astype(float))


def exposure(graph, z, observed=None):
    p = graph.transition if observed is None else observed
    if observed is None:
        # Count binary treated neighbors before dividing. Summing normalized
        # weights can put rational thresholds (60/80=.75,17/20=.85) on the
        # wrong side of a strict/non-strict indicator through roundoff.
        counts = np.asarray(graph.adjacency @ z).ravel()
        s = counts / np.maximum(graph.degree, 1)
        s = np.where(graph.degree == 0, z, s)
    else:
        s = np.asarray(p @ z).ravel()
    t = np.asarray(p @ s).ravel()
    return s, t


def assignment(graph, rng, design="bernoulli", probability=.5):
    if design == "bernoulli":
        return rng.binomial(1, probability, graph.n).astype(float)
    if design == "cluster":
        return rng.binomial(1, probability, graph.clusters.max()+1)[graph.clusters].astype(float)
    raise ValueError(design)


def outcome_mean(graph, z, mechanism, observed=None, gamma=1.):
    s, t = exposure(graph, z, observed)
    if mechanism == "no_interference":
        h = np.zeros(graph.n)
    elif mechanism == "linear":
        h = s
    elif mechanism == "quadratic":
        h = s*s
    elif mechanism == "cubic":
        h = s**3
    elif mechanism == "sigmoid":
        h = (expit(12*(s-.5))-expit(-6))/(expit(6)-expit(-6))
    elif mechanism == "threshold":
        h = (s >= .75).astype(float)
    elif mechanism == "twohop":
        h = .5*(s+t)
    elif mechanism == "hidden_tail":
        # Equal to linear throughout [0.15,0.85]; differs at policy endpoints.
        h = s + np.maximum((s-.85)/.15, 0)**2
    else:
        raise ValueError(mechanism)
    return .5*graph.x + z + gamma*h


def true_gate(graph, mechanism, gamma=1.):
    return float(np.mean(outcome_mean(graph, np.ones(graph.n), mechanism, gamma=gamma)
                         -outcome_mean(graph, np.zeros(graph.n), mechanism, gamma=gamma)))


def noise_operator(graph, rho=0.):
    """Unit marginal variance noise from row-normalized (I + rho P)u."""
    b = sparse.eye(graph.n, format="csr") + rho*graph.transition
    scale = np.sqrt(np.asarray(b.multiply(b).sum(axis=1)).ravel())
    return sparse.diags(1/scale) @ b


def features(graph, z, model, observed=None):
    s, t = exposure(graph, z, observed)
    base = [np.ones(graph.n), z, graph.x]
    if model == "naive":
        # No x adjustment: exactly the treated minus control sample means.
        return np.column_stack(base[:2])
    if model in ("linear", "quadratic", "cubic", "spline", "twohop"):
        base.append(s)
    if model in ("quadratic", "cubic"):
        base.append(s*s)
    if model == "cubic":
        base.append(s**3)
    if model == "twohop":
        base.append(t)
    if model == "threshold_oracle":
        base.append((s >= .75).astype(float))
    if model == "spline":
        # Fixed knots avoid treatment-dependent basis/endpoints and tuning leakage.
        st = SplineTransformer(degree=3, knots=np.linspace(0, 1, 5)[:, None],
                               include_bias=False, extrapolation="linear")
        st.fit(np.linspace(0, 1, 11)[:, None])
        # Centered spline basis; omit raw s to avoid exact linear dependence.
        base = base[:3] + [v for v in st.transform(s[:, None]).T]
    if model not in ("naive", "linear", "quadratic", "cubic", "spline", "twohop", "threshold_oracle"):
        raise ValueError(model)
    return np.column_stack(base)


def contrast_weights(graph, z, model, observed=None):
    x = features(graph, z, model, observed)
    c = np.mean(features(graph, np.ones(graph.n), model, observed)
                - features(graph, np.zeros(graph.n), model, observed), axis=0)
    # SVD gives both the minimum-norm solution and estimability diagnostics.
    u, singular, vt = np.linalg.svd(x, full_matrices=False)
    tol = np.finfo(float).eps * max(x.shape) * singular[0]
    keep = singular > tol
    v = vt[keep].T
    c_projected = v @ (v.T @ c)
    estimability = np.linalg.norm(c-c_projected)
    xinv = (v/singular[keep]) @ u[:, keep].T
    a = c @ xinv
    leverage = np.sum(u[:, keep]**2, axis=1)
    return x, c, xinv, a, leverage, int(keep.sum()), float(estimability), singular


def regression(graph, z, y, mean, truth, noise_map, model, observed=None, prepared=None):
    x, c, xinv, a, h, rank, estimability, singular = (contrast_weights(graph, z, model, observed)
                                                   if prepared is None else prepared)
    if model=="naive" and (np.sum(z)==0 or np.sum(z)==graph.n):
        result={name:np.nan for name in ['estimate','error','conditional_bias','oracle_variance',
                'conditional_mse','weight_norm2','max_abs_weight','hc3_se','oracle_se',
                'cover_hc3','cover_oracle','outcome_rmse','condition']}
        result.update(rank=rank,n_features=x.shape[1],estimability_error=estimability,
                      valid=False,failure_reason="empty_arm")
        return result
    pred = x @ (xinv @ y)
    resid = y-pred
    oracle_variance = float(np.sum(np.asarray(noise_map.T @ a).ravel()**2))
    hc3_variance = float(np.sum((a*resid/np.maximum(1-h, 1e-10))**2))
    conditional_bias = float(a @ mean-truth)
    estimate = float(a @ y)
    return dict(estimate=estimate, error=estimate-truth, conditional_bias=conditional_bias,
                oracle_variance=oracle_variance, conditional_mse=conditional_bias**2+oracle_variance,
                weight_norm2=float(a@a), max_abs_weight=float(np.abs(a).max()),
                hc3_se=np.sqrt(hc3_variance), oracle_se=np.sqrt(oracle_variance),
                cover_hc3=abs(estimate-truth)<=1.959963984540054*np.sqrt(hc3_variance),
                cover_oracle=abs(estimate-truth)<=1.959963984540054*np.sqrt(oracle_variance),
                outcome_rmse=float(np.sqrt(np.mean(resid**2))), rank=rank,
                n_features=x.shape[1], estimability_error=estimability,
                condition=float(singular[0]/singular[-1]) if singular[-1]>0 else np.inf,
                valid=estimability<1e-8)


def exposure_probabilities(graph, design, probability=.5):
    """Probability of full own+neighbor treatment/control, with cluster sharing."""
    if design == "bernoulli":
        count = graph.degree.astype(int)+1
    elif design == "cluster":
        a = graph.adjacency
        count = np.array([len(np.unique(graph.clusters[np.r_[i, a.indices[a.indptr[i]:a.indptr[i+1]]]]))
                          for i in range(graph.n)])
    else:
        raise ValueError(design)
    return probability**count, (1-probability)**count


def full_exposure_estimates(graph, z, y, probabilities):
    """Full-neighborhood HT and Hajek: unstable/undefined cases stay visible."""
    a = graph.adjacency
    treated = (z == 1) & (np.asarray(a @ (1-z)).ravel() == 0)
    control = (z == 0) & (np.asarray(a @ z).ravel() == 0)
    pt, pc = probabilities
    # Evaluate observed nonzero terms only, avoiding 0/underflow in absent units.
    wt = 1/pt[treated]
    wc = 1/pc[control]
    ht = (wt@y[treated]-wc@y[control])/graph.n
    hajek = wt@y[treated]/wt.sum()-wc@y[control]/wc.sum() if wt.size and wc.size else np.nan
    return dict(ht=float(ht), hajek=float(hajek), full_treated=int(treated.sum()),
                full_control=int(control.sum()), min_log_probability=float(np.log(pt).min()) if np.all(pt>0) else -np.inf)
