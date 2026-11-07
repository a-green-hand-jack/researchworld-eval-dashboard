"""Dataset access: each dataset yields (Y, f, truth, extras) for the iid superpopulation = empirical distribution."""
import numpy as np, os

DATA_DIR = os.environ.get("PPI_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DATASETS = ["galaxies", "forest", "alphafold", "gene_expression", "census_income",
            "census_healthcare", "census_education", "ballots", "plankton"]


def load(name):
    from ppi_py.datasets import load_dataset
    d = load_dataset(DATA_DIR + "/", name)
    return {k: np.asarray(v) for k, v in d.items()}


def population(name):
    """Return dict(Y, f, theta) for the labeled population; theta = mean of Y over it.

    plankton additionally returns f_unl_pool / theta_unl for the covariate-shift study.
    """
    d = load(name)
    out = {"Y": d["Y"].astype(float), "f": d["Yhat"].astype(float)}
    out["theta"] = out["Y"].mean()
    if name == "plankton":
        out["f_shift"] = d["Yhat_unlabeled"].astype(float)
        out["Y_shift"] = d["Y_unlabeled"].astype(float)
        out["theta_shift"] = out["Y_shift"].mean()
    return out


# ---------------- synthetic populations with known truth ----------------
def _std(x):
    return (x - x.mean()) / x.std()


def synth_sampler(kind, kappa=0.0, snr=1.0, tail=0):
    """Return (sampler(rng, m) -> (Y, f), theta, info). f ~ N(0,1) is the *fixed predictor output*.

    kind='gauss': Y = g_kappa(f) + eps, g = (1-kappa)*f + kappa*h(f), h standardized nonlinear shape
        (h = 'quad': f^2-1 over sqrt2 -- U-shape; 'tanh': tanh(2f)/sd -- saturation); eps ~ N(0, sigma_e^2).
        theta = E[Y] = 0.
    kind='bin': Y ~ Bernoulli(sigmoid(a*logit(f_prob)+b)) where f_prob = sigmoid(3 z) is an *overconfident or
        calibrated* classifier output; kappa in [0,1] interpolates temperature a = 1 - 0.8*kappa (a=1 calibrated).
    """
    from scipy.special import expit, logit
    if kind in ("quad", "tanh"):
        def h(f):
            return (f ** 2 - 1) / np.sqrt(2) if kind == "quad" else np.tanh(2 * f) / 0.7
        # signal variance normalised to 1; noise variance 1/snr
        lin = np.sqrt(1 - kappa)
        non = np.sqrt(kappa)

        def sampler(rng, m):
            f = rng.standard_normal(m)
            g = lin * f + non * h(f)
            eps = rng.standard_t(3, m) / np.sqrt(3.0) if tail else rng.standard_normal(m)   # t3 noise, unit variance
            return g + eps / np.sqrt(snr), f
        return sampler, 0.0, dict(kind=kind, kappa=kappa, snr=snr)
    if kind == "bin":
        a = 1 - 0.8 * kappa

        def sampler(rng, m):
            z = rng.standard_normal(m) * snr
            fp = expit(3 * z)
            y = (rng.random(m) < expit(a * logit(fp) - 1.0)).astype(float)
            return y, fp
        rng = np.random.default_rng(12345)
        y, _ = sampler(rng, 20_000_000)
        return sampler, float(y.mean()), dict(kind=kind, kappa=kappa, snr=snr)
    raise ValueError(kind)
