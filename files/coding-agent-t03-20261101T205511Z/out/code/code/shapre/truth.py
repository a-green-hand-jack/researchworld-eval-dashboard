"""'Truth' for the attribution of f=P(y=1) w.r.t. a background Z: exact if cheap, else high-budget reference
(own antithetic permutation sampler with `ref_coal` coalition evaluations; its SE is returned)."""
import numpy as np
from . import exact, estimators as E
from .config import REF_COALITIONS


def truth(model, x, Z, ref_seed=0, ref_coal=REF_COALITIONS, enum_d=20, force_ref=False):
    """returns phi (d,), se (d,) (zeros if exact), kind in {'exact','ref'}"""
    d = len(x)
    is_net = hasattr(model, "rest")
    if not force_ref:
        if (not is_net) and model.kind == "rf":
            return exact.exact_tree(model, x, Z), np.zeros(d), "exact"
        if is_net and d <= enum_d:
            return exact.exact_net(model, x, Z), np.zeros(d), "exact"
        if model.kind == "xgb" and d <= 10:
            return exact.exact_bruteforce(model.predict, x, Z), np.zeros(d), "exact"
    phi, se, _ = E.perm_own(model, x, Z, ref_coal, ref_seed)
    return phi, se, "ref"
