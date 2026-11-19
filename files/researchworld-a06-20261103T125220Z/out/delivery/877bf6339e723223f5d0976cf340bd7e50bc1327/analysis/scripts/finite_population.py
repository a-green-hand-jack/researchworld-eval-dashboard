"""Exact equal-tailed hypergeometric interval for a finite-population accuracy."""
from scipy.stats import hypergeom


def hypergeom_interval(successes, sample_size, population_size, alpha=.05):
    """Invert both tails for total successes M; return M/N endpoints.

    A simple random sample without replacement is required. Discreteness can
    make coverage conservative. Equality is included at the tail cutoff.
    """
    x=int(successes);m=int(sample_size);N=int(population_size)
    assert 0<=x<=m<=N and N>0 and 0<alpha<1
    possible_lo=x;possible_hi=N-m+x
    lo,hi=possible_lo,possible_hi
    while lo<hi:
        mid=(lo+hi)//2
        if hypergeom.sf(x-1,N,mid,m)>=alpha/2:hi=mid
        else:lo=mid+1
    lower=lo
    lo,hi=possible_lo,possible_hi
    while lo<hi:
        mid=(lo+hi+1)//2
        if hypergeom.cdf(x,N,mid,m)>=alpha/2:lo=mid
        else:hi=mid-1
    return lower/N,lo/N


def paired_difference_interval(wins, losses, sample_size, population_size, alpha=.05):
    """Conservative exact interval for paired binary-accuracy contrast.

    Wins/losses are disjoint item categories. Marginal hypergeometric
    intervals at alpha/2 protect both category proportions by a union bound;
    subtract their endpoints, retaining pairing without an independence claim.
    """
    assert wins+losses<=sample_size
    win_lo,win_hi=hypergeom_interval(wins,sample_size,population_size,alpha/2)
    loss_lo,loss_hi=hypergeom_interval(losses,sample_size,population_size,alpha/2)
    return win_lo-loss_hi,win_hi-loss_lo
