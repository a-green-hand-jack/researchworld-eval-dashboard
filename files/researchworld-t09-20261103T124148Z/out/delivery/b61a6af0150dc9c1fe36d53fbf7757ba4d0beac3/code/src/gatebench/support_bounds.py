"""Exact marginal tail probabilities and a coupling risk lower bound.

For regular graphs under node Bernoulli(p), each node's neighbor count is
Binomial(d,p). Dependence between nodes is handled by a union bound, never by
pretending their exposures are independent.
"""
import json
from pathlib import Path
import numpy as np
from scipy.stats import binom


def regular_bounds(n, degree, p=.5, gamma=1.):
    # hidden_tail differs from linear iff S>.85; strict inequality matters.
    k=int(np.floor(.85*degree))+1
    tail=float(binom.sf(k-1,degree,p))
    union_upper=min(1.,n*tail)
    raw_lower=max(0.,1-union_upper)
    probability_equal_lower=float(np.nextafter(raw_lower,-np.inf)) if raw_lower>0 else 0.
    return dict(n=n,degree=degree,p=p,gamma=gamma,tail_min_treated_neighbors=k,
                marginal_tail_probability=tail,event_unequal_data_probability_upper=union_upper,
                event_identical_data_probability_lower=probability_equal_lower,
                max_two_model_mse_lower_bound=gamma**2/4*probability_equal_lower,
                threshold_positive_probability=float(binom.sf(int(np.ceil(.75*degree))-1,degree,p)),
                expected_full_treated_per_assignment=n*p**(degree+1),
                expected_full_control_per_assignment=n*(1-p)**(degree+1))

if __name__=='__main__':
    rows=[regular_bounds(n,d,p) for n,d in [(2000,4),(2000,20),(2000,80),(8000,20)]
          for p in [.2,.5,.8]]
    out=Path('results/support_bounds.json');out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(rows,indent=2));print(out)
