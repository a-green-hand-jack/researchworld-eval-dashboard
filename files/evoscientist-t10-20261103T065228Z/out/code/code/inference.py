"""Fixed-score mean inference. No function modifies the supplied score/predictor.
All normal intervals are asymptotic, not finite-sample claims.
"""
from functools import lru_cache
import numpy as np
from scipy.stats import beta as beta_dist, norm

ALPHA = 0.05
ZCRIT = float(norm.ppf(1 - ALPHA / 2))


def sample_var(x):
    return float(np.var(x, ddof=1))


def normal_ci(center, variance):
    radius = ZCRIT * np.sqrt(max(0.0, variance))
    # Intersecting with the known parameter space preserves coverage.
    return max(0.0, center - radius), min(1.0, center + radius), float(center)


def eb_radius(x, span, delta=ALPHA):
    """Two-sided Maurer--Pontil Thm 4, union over tails.
    x are iid within a known interval of length span, conditional on any pilot.
    """
    m = len(x)
    if m < 2:
        raise ValueError('at least two iid observations required')
    log = np.log(4.0 / delta)
    return np.sqrt(2.0 * sample_var(x) * log / m) + 7.0 * span * log / (3.0 * (m - 1))


def eb_mean(x):
    center = float(np.mean(x))
    rad = eb_radius(x, 1.0)
    return max(0.0, center-rad), min(1.0, center+rad), center


@lru_cache(maxsize=100000)
def clopper_pearson(k, n, alpha=ALPHA):
    if not isinstance(n,(int,np.integer)) or not isinstance(k,(int,np.integer)) or n<1 or not 0<=k<=n or not 0<alpha<1:
        raise ValueError('integer count 0<=k<=n, n>=1 and 0<alpha<1 required')
    lo = 0.0 if k == 0 else float(beta_dist.ppf(alpha/2, k, n-k+1))
    hi = 1.0 if k == n else float(beta_dist.ppf(1-alpha/2, k+1, n-k))
    return lo, hi, k/n


def pooled_variance(z, u):
    n, N = len(z), len(u)
    anchor = float(z[0])
    z, u = z-anchor, u-anchor
    mz, mu = float(z.mean()), float(u.mean())
    # Stable centered within-/between-group decomposition, never E[Z^2]-E[Z]^2.
    dz, du = z-mz, u-mu
    return float((dz@dz + du@du + (n*N/(n+N))*(mz-mu)**2)/(n+N-1))


def ppi(y, z, u, tuned=True):
    n, N = len(y), len(u)
    # Subtract a common anchor BEFORE means or large coefficients are applied.
    # This only changes a cancelling intercept, not the control or base scores.
    anchor = float(z[0])
    z, u = z-anchor, u-anchor
    vp = pooled_variance(z, u)
    cov = float(np.dot(y-y.mean(), z-z.mean())/(n-1))
    lam = cov / ((1+n/N)*vp) if tuned and vp > 0.0 else (0.0 if tuned else 1.0)
    center = float(y.mean() + lam*(u.mean()-z.mean()))
    # Published PPI++ pooled prediction-variance convention.
    vu = vp if tuned else sample_var(u)
    out = normal_ci(center, sample_var(y-lam*z)/n + lam*lam*vu/N)
    return out


def bins(z, B):
    return np.clip((z * B).astype(int), 0, B-1)


def fit_hist(y, z, B=4, pseudo=2.0):
    b = bins(z, B)
    count = np.bincount(b, minlength=B)
    sy = np.bincount(b, weights=y, minlength=B)
    return (sy + pseudo*y.mean()) / (count+pseudo)


def hist_plugin(y, z, u, B=4):
    """Same-label fixed-dimensional plug-in; asymptotic only."""
    n, N = len(y), len(u)
    g = fit_hist(y, z, B) * (N/(N+n))
    h, hu = g[bins(z, B)], g[bins(u, B)]
    center = float(np.mean(y-h)+np.mean(hu))
    return normal_ci(center, sample_var(y-h)/n + sample_var(hu)/N)


def cross_hist(y, z, u, B=4, K=5):
    n, N = len(y), len(u)
    if n % K or N % K:
        raise ValueError('balanced folds required')
    b, bu = bins(z, B), bins(u, B)
    nk, Nk = n//K, N//K
    counts = np.bincount(b, minlength=B)
    sums = np.bincount(b, weights=y, minlength=B)
    a = N/(N+n)
    center = variance = 0.0
    for k in range(K):
        sl, su = slice(k*nk,(k+1)*nk), slice(k*Nk,(k+1)*Nk)
        c = counts - np.bincount(b[sl], minlength=B)
        s = sums - np.bincount(b[sl], weights=y[sl], minlength=B)
        trainmean = (y.sum()-y[sl].sum())/(n-nk)
        g = a*(s+2*trainmean)/(c+2)
        r, hu = y[sl]-g[b[sl]], g[bu[su]]
        center += (r.mean()+hu.mean())/K
        variance += (sample_var(r)/nk + sample_var(hu)/Nk)/(K*K)
    return normal_ci(center, variance)


def series(y, z, u, B=4):
    """Nested affine+histogram vector PPI++ with vanishing ridge.
    Features are z and indicators for bins 0,...,B-2. Constants cancel.
    """
    n, N = len(y), len(u)
    b, bu = bins(z, B), bins(u, B)
    anchor = float(z[0])
    z, u = z-anchor, u-anchor
    def moments(s, bi):
        cnt = np.bincount(bi, minlength=B)[:-1].astype(float)
        bs = np.bincount(bi, weights=s, minlength=B)[:-1]
        sm = np.r_[s.sum(), cnt]
        ss = np.zeros((B,B))
        ss[0,0] = s@s
        ss[0,1:] = ss[1:,0] = bs
        ss[1:,1:] = np.diag(cnt)
        return sm, ss
    sl, ql = moments(z,b)
    su, qu = moments(u,bu)
    mean = (sl+su)/(n+N)
    G = (ql+qu-(n+N)*np.outer(mean,mean))/(n+N-1)
    xy = np.r_[y@z, np.bincount(b, weights=y, minlength=B)[:-1]]
    cov = (xy-y.sum()*sl/n)/(n-1)
    coef = np.linalg.solve(G + (1e-3/n)*np.eye(B), cov)/(1+n/N)
    offset = np.r_[coef[1:],0.0]
    h, hu = coef[0]*z+offset[b], coef[0]*u+offset[bu]
    center = float(y.mean() + np.dot(coef, su/N-sl/n))
    vu = float(coef@G@coef)
    return normal_ci(center, sample_var(y-h)/n+vu/N)


def split_controls(y, z, u, B=4):
    """Pilot uses 20% of same label budget. All three controls share the split.
    Conditional on pilot, h is fixed, in [0,a]; residual span=1+a.
    """
    n = len(y)
    p = n//5
    yp, zp, yr, zr = y[:p], z[:p], y[p:], z[p:]
    m, N = len(yr), len(u)
    a = N/(N+m)
    hist = a*fit_hist(yp,zp,B)
    v = sample_var(zp)
    slope = float(np.cov(yp,zp,ddof=1)[0,1]/v) if v>0.0 else 0.0
    intercept = float(yp.mean()-slope*zp.mean())
    controls = {
        'Raw': (a*zr, a*u),
        'Linear': (a*np.clip(intercept+slope*zr,0,1), a*np.clip(intercept+slope*u,0,1)),
        'Hist4': (hist[bins(zr,B)], hist[bins(u,B)])
    }
    out = {'EBLabelSplit':eb_mean(yr)}
    for name,(h,hu) in controls.items():
        r = yr-h
        center = float(r.mean()+hu.mean())
        radius = eb_radius(r,1+a,ALPHA/2)+eb_radius(hu,a,ALPHA/2)
        out['EB'+name] = (max(0.,center-radius),min(1.,center+radius),center)
        out['SplitWald'+name] = normal_ci(center,sample_var(r)/m+sample_var(hu)/N)
    return out


def evaluate(y, z, u, oracle=None, ablate=False):
    y,z,u = np.asarray(y,float),np.asarray(z,float),np.asarray(u,float)
    if any(a.ndim != 1 for a in (y,z,u)) or len(y)!=len(z):
        raise ValueError('aligned one-dimensional label/score arrays required')
    if any(not np.all(np.isfinite(a)) for a in (y,z,u)):
        raise ValueError('finite observations required')
    if not np.all((y==0)|(y==1)):
        raise ValueError('this evaluator requires binary labels for binomial intervals')
    if np.any((z<0)|(z>1)) or np.any((u<0)|(u>1)):
        raise ValueError('scores must be bounded in [0,1]')
    n,N = len(y),len(u)
    if n<10 or N<10 or n%5 or N%5:
        raise ValueError('complete evaluator requires n,N>=10 divisible by five')
    out = {
        'LabelWald': normal_ci(float(y.mean()),sample_var(y)/n),
        'LabelCP': clopper_pearson(int(y.sum()),n),
        'PPI':ppi(y,z,u,False),
        'PPI++':ppi(y,z,u,True),
        'Hist4':hist_plugin(y,z,u,4),
        'CFHist4':cross_hist(y,z,u,4),
        'Series4':series(y,z,u,4),
        'EBLabel':eb_mean(y)
    }
    out.update(split_controls(y,z,u))
    if oracle is not None:
        a=N/(N+n)
        h,hu=a*oracle(z),a*oracle(u)
        out['Oracle']=normal_ci(float(np.mean(y-h)+np.mean(hu)),sample_var(y-h)/n+sample_var(hu)/N)
    if ablate:
        for B in [1,2,8,16]:
            out[f'CFHist{B}']=cross_hist(y,z,u,B)
            out[f'Series{B}']=series(y,z,u,B)
    # Numeric intervals may be empty if an estimate is far outside parameter space.
    # Preserve emptiness; width=0 and coverage=False, not reversed endpoints.
    return out
