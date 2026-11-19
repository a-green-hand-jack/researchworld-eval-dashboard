from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from scipy.stats import binom,binomtest
from scipy.special import logsumexp
from analyze import holm_log,scientific_log


def test_extreme_tail_and_holm_no_underflow():
    logp=logsumexp(binom.logpmf(np.arange(530),2000,.95))
    assert np.isfinite(logp) and logp < -1000
    assert 'e-' in scientific_log(logp)
    adjusted=holm_log([logp,logp-100,np.log(.04)])
    assert np.isfinite(adjusted).all()
    assert np.all(adjusted >= np.array([logp,logp-100,np.log(.04)]))
    assert np.all(adjusted<=0)


def test_representable_binomial_tail_matches_scipy():
    k=1871;n=2000
    logp=logsumexp(binom.logpmf(np.arange(k+1),n,.95))
    np.testing.assert_allclose(np.exp(logp),binomtest(k,n,.95,alternative='less').pvalue,rtol=1e-10)
