"""Nonconformity scores for simplex-valued targets: s(y, yhat, sigma) -> distance-like.

All are 'larger = more nonconforming'; a region is {y : s(y, yhat(x), sigma(x)) <= q}.
`yhat` and `y` broadcast over leading dims; last axis is the K components.
"""
import numpy as np
from .simplex import clr, EPS

SCORES = {}


def register(name):
    def deco(f):
        SCORES[name] = f
        return f
    return deco


@register("euc")
def euc(y, yh):
    return np.sqrt(((y - yh) ** 2).sum(-1))


@register("l1")
def l1(y, yh):
    return np.abs(y - yh).sum(-1)


@register("hell")
def hell(y, yh):
    return np.sqrt(((np.sqrt(y) - np.sqrt(yh)) ** 2).sum(-1))


@register("aitch")
def aitch(y, yh):
    return np.sqrt(((clr(y) - clr(yh)) ** 2).sum(-1))


@register("kl_fwd")
def kl_fwd(y, yh):
    # KL(y || yh)
    y = np.maximum(y, EPS)
    return (y * (np.log(y) - np.log(np.maximum(yh, EPS)))).sum(-1)


@register("kl_rev")
def kl_rev(y, yh):
    # KL(yh || y): blows up near the boundary of y
    y = np.maximum(y, EPS)
    return (yh * (np.log(np.maximum(yh, EPS)) - np.log(y))).sum(-1)


BASE_SCORES = list(SCORES)


def score(name, y, yh, sig=None):
    """name may be 'euc' or 'euc/n' (normalised by sigma(x))."""
    if name.endswith("/n"):
        return SCORES[name[:-2]](y, yh) / sig
    return SCORES[name](y, yh)
