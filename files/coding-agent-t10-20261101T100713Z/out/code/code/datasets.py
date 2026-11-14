"""Populations from which (labeled, unlabeled) samples are drawn i.i.d.

Real data: the full file is treated as the population (empirical distribution); samples are drawn
with replacement, so the labeled and unlabeled sets are exactly i.i.d. from it and the target
theta = mean(Y) over the file is the exact truth.
Synthetic data: closed-form generators with analytic truth.
"""
import os
import numpy as np

DATA_DIR = os.environ.get("PPI_DATA_DIR", "/work/data")
REAL = ["galaxies", "forest", "alphafold", "gene_expression", "census_income",
        "census_healthcare", "census_education", "plankton", "ballots"]


class RealPop:
    def __init__(self, name):
        d = np.load(os.path.join(DATA_DIR, name + ".npz"))
        self.name = name
        self.Y = d["Y"].astype(float)
        self.F = d["Yhat"].astype(float)
        if "X" in d:
            self.X = d["X"].astype(float)
        elif "phosphorylated" in d:
            self.X = np.c_[d["phosphorylated"], d["ubiquitinated"], d["acetylated"]].astype(float)
        else:
            self.X = np.zeros((len(self.Y), 0))
        self.truth = float(self.Y.mean())

    def draw(self, rng, m):
        i = rng.integers(0, len(self.Y), m)
        return self.Y[i], self.F[i], self.X[i]


class SynthPop:
    def __init__(self, name, fn, truth, p):
        self.name, self.fn, self.truth, self.p = name, fn, truth, p

    def draw(self, rng, m):
        Y, F, X = self.fn(rng, m)
        return Y, F, (X if X is not None else np.zeros((m, 0)))


def _sig(x):
    return 1 / (1 + np.exp(-x))


def _s0(r, m):  # calibrated predictor, nothing left to gain
    x1 = r.normal(size=m); return x1 + r.normal(size=m), x1, None

def _s1(r, m):  # predictor monotone but non-linearly related to E[Y|F]
    x1 = r.normal(size=m); return np.exp(x1) + 0.5 * r.normal(size=m), x1, None

def _s2(r, m):  # label depends linearly on a covariate the predictor ignores
    x1, x2 = r.normal(size=(2, m)); return x1 + x2 + 0.5 * r.normal(size=m), x1, x2[:, None]

def _s3(r, m):  # ... nonlinearly
    x1, x2 = r.normal(size=(2, m)); return x1 + 1.5 * np.sin(2 * x2) + 0.5 * r.normal(size=m), x1, x2[:, None]

def _s4(r, m):  # predictor is pure noise, covariate informative
    x1, f = r.normal(size=(2, m)); return x1 + 0.5 * r.normal(size=m), f, x1[:, None]

def _s5(r, m):  # predictor and covariates are all pure noise
    x1, f = r.normal(size=(2, m)); return x1 + r.normal(size=m), f, r.normal(size=(m, 2))

def _s6(r, m):  # calibrated predictor, heavy-tailed noise
    x1 = r.normal(size=m); return x1 + r.standard_t(3, size=m), x1, None

def _s7(r, m):  # binary label, miscalibrated probability predictor
    x1 = r.normal(size=m); return (r.uniform(size=m) < _sig(2 * x1)).astype(float), _sig(x1), None


SYNTH = {
    "S0_calibrated": SynthPop("S0_calibrated", _s0, 0.0, 0),
    "S1_nonlinear_link": SynthPop("S1_nonlinear_link", _s1, float(np.exp(0.5)), 0),
    "S2_omitted_linear": SynthPop("S2_omitted_linear", _s2, 0.0, 1),
    "S3_omitted_nonlinear": SynthPop("S3_omitted_nonlinear", _s3, 0.0, 1),
    "S4_noise_predictor": SynthPop("S4_noise_predictor", _s4, 0.0, 1),
    "S5_all_noise": SynthPop("S5_all_noise", _s5, 0.0, 2),
    "S6_heavy_tail": SynthPop("S6_heavy_tail", _s6, 0.0, 0),
    "S7_binary_miscal": SynthPop("S7_binary_miscal", _s7, 0.5, 0),
}


def get_pop(name):
    return SYNTH[name] if name in SYNTH else RealPop(name)


def learners_for(pop):
    p = pop.X.shape[1] if isinstance(pop, RealPop) else pop.p
    return ["lin", "iso"] + (["linX", "gbm"] if p > 0 else [])
