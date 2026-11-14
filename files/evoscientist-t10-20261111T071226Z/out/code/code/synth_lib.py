"""Synthetic experiments with known truth.  Usage: python run_synth.py [reps]
Outputs: results/synth_summary.csv (per scenario/n/N/method), results/synth_theory.csv"""
import sys, os, itertools, time
os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ.get('PYTHONPATH', '')
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import norm
from scipy.special import expit
from common import run_reps, summarize, asym_variances, theory_ratio

BASE_SEED = 20261111
SQ2 = np.sqrt(2.0)


def make_scenarios():
    S = {}
    # name -> dict(kind, g(z), noise_var, theta0, fscale, truth)
    gh_x, gh_w = np.polynomial.hermite_e.hermegauss(80)
    gh_w = gh_w / gh_w.sum()
    Egh = lambda fn: float(np.sum(gh_w * fn(gh_x)))
    for deg in (0, 30, 60, 90):
        phi = np.deg2rad(deg)
        S[f"herm{deg}"] = dict(kind="gauss", g=lambda z, p=phi: np.cos(p) * z + np.sin(p) * (z ** 2 - 1) / SQ2,
                               nv=1.0, theta0=1.0, fscale=1.0, truth=1.0, rho2=np.cos(phi) ** 2)
    for beta in (1.0, 1.5):
        sd = np.sqrt(np.exp(beta ** 2) * (np.exp(beta ** 2) - 1))
        S[f"lognorm{beta:g}"] = dict(kind="gauss", g=lambda z, b=beta, s=sd: (np.exp(b * z) - np.exp(b * b / 2)) / s,
                                     nv=1.0, theta0=1.0, fscale=1.0, truth=1.0)
    for b in (1.0, 3.0):
        gf = lambda z, b=b: expit(-1.0 + b * z)
        S[f"logistic{b:g}"] = dict(kind="bern", g=gf, theta0=0.0, fscale=1.0, truth=Egh(gf))
    S["binaryf"] = dict(kind="binf", theta0=0.0, fscale=1.0, truth=0.1 * 0.7 + 0.7 * 0.3)
    S["herm0_scale0.25"] = dict(S["herm0"], fscale=0.25)
    S["herm30_scale0.25"] = dict(S["herm30"], fscale=0.25)
    return S


def draw_fn(sc, n, N):
    kind = sc["kind"]

    def draw(rng):
        if kind == "binf":
            f = (rng.random(n + N) < 0.3).astype(float)
            g = np.where(f == 1, 0.7, 0.1)
            Y = (rng.random(n) < g[:n]).astype(float)
            return Y, f[:n], f[n:]
        z = rng.standard_normal(n + N)
        g = sc["g"](z)
        if kind == "gauss":
            Y = sc["theta0"] + g[:n] + np.sqrt(sc["nv"]) * rng.standard_normal(n)
        else:
            Y = (rng.random(n) < g[:n]).astype(float)
        f = sc["fscale"] * z
        return Y, f[:n], f[n:]
    return draw


def theory_for(sc, n, N, M=1_000_000):
    """Asymptotic variances via a deterministic quantile grid of the predictor distribution."""
    if sc["kind"] == "binf":
        f = np.concatenate([np.zeros(700), np.ones(300)])
        g = np.where(f == 1, 0.7, 0.1)
        EV = g * (1 - g)
    else:
        z = norm.ppf((np.arange(M) + 0.5) / M)
        g = sc["g"](z)
        f = sc["fscale"] * z
        EV = np.full(M, sc["nv"]) if sc["kind"] == "gauss" else g * (1 - g)
    return asym_variances(g, EV, f, n, N)


def one_config(cid, name, n, N, R):
    sc = make_scenarios()[name]
    seed = int(np.random.SeedSequence([BASE_SEED, cid]).generate_state(1)[0])
    th, se = run_reps(draw_fn(sc, n, N), sc["truth"], R, seed)
    rows = summarize(th, se, sc["truth"])
    tv = theory_for(sc, n, N)
    tr = theory_ratio(tv)
    for r in rows:
        r.update(scenario=name, n=n, N=N, theory_ratio=tr.get(r["method"], np.nan),
                 theory_ratio_eff=tr["efficient"])
    return rows


