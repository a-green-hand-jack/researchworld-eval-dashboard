"""CPU-only, aggregated ridge Bradley--Terry fits and auditable flip paths."""
from dataclasses import dataclass
import numpy as np
from scipy.special import expit
from scipy.linalg import solve


@dataclass
class Panel:
    name: str
    models: list
    a: np.ndarray
    b: np.ndarray
    y: np.ndarray
    cluster: np.ndarray
    home: np.ndarray | None = None

    def __post_init__(self):
        self.a = np.asarray(self.a, dtype=int)
        self.b = np.asarray(self.b, dtype=int)
        self.y = np.asarray(self.y, dtype=float)
        self.cluster = np.asarray(self.cluster)
        self.m = len(self.models)
        self.n = len(self.y)
        keys = np.column_stack([self.a,self.b] + ([] if self.home is None else [self.home]))
        unique, self.group = np.unique(keys, axis=0, return_inverse=True)
        x = np.zeros((len(unique), self.m + (self.home is not None)))
        x[np.arange(len(unique)), unique[:,0].astype(int)] = 1
        x[np.arange(len(unique)), unique[:,1].astype(int)] -= 1
        if self.home is not None:
            x[:, -1] = unique[:,2]
        self.X = x
        self.count = np.bincount(self.group, minlength=len(self.X)).astype(float)
        self.wins = np.bincount(self.group, weights=self.y, minlength=len(self.X))

    def subset(self, ids, name=None):
        return Panel(name or self.name, self.models, self.a[ids], self.b[ids],
                     self.y[ids], self.cluster[ids],
                     None if self.home is None else self.home[ids])


class BT:
    def __init__(self, panel, ridge=1.):
        self.panel = panel
        self.X = panel.X
        self.ridge = ridge
        self.fit_count = 0
        self.max_residual = 0.

    def fit(self, count=None, wins=None, start=None, linear=None):
        count = self.panel.count if count is None else count
        wins = self.panel.wins if wins is None else wins
        t = np.zeros(self.X.shape[1]) if start is None else start.copy()
        X, lam = self.X, self.ridge
        linear = np.zeros(len(t)) if linear is None else linear
        def objective(v):
            z = X @ v
            return count @ np.logaddexp(0, z) - wins @ z + lam/2 * (v @ v) + linear@v
        for iteration in range(80):
            z = X @ t
            p = expit(z)
            g = X.T @ (count*p-wins)+lam*t+linear
            H = (X.T*(count*p*(1-p))) @ X+lam*np.eye(len(t))
            if np.max(np.abs(g)) < 2e-8:
                break
            step = solve(H, g, assume_a='pos')
            # Near convergence objective differences lose precision; Newton's
            # local step is more reliable than Armijo in this regime.
            if np.max(np.abs(step)) < 1e-7:
                t -= step
                continue
            value = objective(t)
            rate = 1.
            while objective(t-rate*step) > value - 1e-4*rate*(g@step) + 1e-10:
                rate /= 2
                if rate < 2**-30:
                    raise RuntimeError('Newton line search failed')
            t -= rate*step
        z = X@t
        residual = float(np.max(np.abs(X.T@(count*expit(z)-wins)+lam*t+linear)))
        if residual > 1e-6:
            raise RuntimeError(f'Fit residual {residual}; {self.panel.name}')
        self.fit_count += 1
        self.max_residual = max(self.max_residual, residual)
        return t

    def hessian(self, t):
        p = expit(self.X @ t)
        return (self.X.T*(self.panel.count*p*(1-p)))@self.X+self.ridge*np.eye(len(t))

    def contrast(self, first, second):
        c = np.zeros(self.X.shape[1]); c[first] = 1; c[second] = -1
        return c

    def gains(self, t, c, mode='flip'):
        v = solve(self.hessian(t), c, assume_a='pos')
        xp = self.X@v
        if mode == 'flip':
            return (2*self.panel.y-1)*xp[self.panel.group]
        if mode == 'delete':
            return (self.panel.y-expit(self.X@t)[self.panel.group])*xp[self.panel.group]
        raise ValueError(mode)

    def attack(self, t, c, mode='flip', scope='all', cap=None, margin=0., adaptive=False):
        """Static influence order; refit EVERY integer prefix until crossing.

        A returned k is the first feasible prefix of this specific order, and
        an upper bound on the optimal edit count. No global optimality claim.
        """
        p = self.panel
        initial_gap = float(c@t)+margin
        if initial_gap < -1e-9:
            return dict(k=0, predicted_k=0, gap=initial_gap, ids=[], trace=[])
        gains = self.gains(t, c, mode)
        eligible = ((p.y == 0) | (p.y == 1)) if mode == 'flip' else np.ones(p.n, bool)
        if scope == 'incident':
            targets = np.flatnonzero(c[:p.m])
            eligible &= np.isin(p.a, targets) | np.isin(p.b, targets)
        ids = np.flatnonzero(eligible & (gains > 1e-14))
        ids = ids[np.argsort(-gains[ids], kind='stable')]
        limit = len(ids) if cap is None else min(len(ids), cap)
        cum = np.cumsum(gains[ids])
        cross = np.flatnonzero(cum > initial_gap)
        pred = int(cross[0]+1) if len(cross) else None
        count, wins = p.count.copy(), p.wins.copy()
        current = t.copy()
        trace = []
        used=[]
        available=eligible.copy()
        for k in range(1,limit+1):
            if adaptive:
                gg=self.gains(current,c,mode)
                gg[~available]=-np.inf
                row=int(np.argmax(gg))
                if gg[row]<=1e-14: break
            else: row=ids[k-1]
            available[row]=False
            used.append(int(row))
            j = p.group[row]
            if mode == 'flip':
                wins[j] += 1-2*p.y[row]
            else:
                count[j] -= 1; wins[j] -= p.y[row]
            current = self.fit(count, wins, current)
            gap = float(c@current)
            trace.append(gap)
            if gap+margin < -1e-9:
                return dict(k=k, predicted_k=pred, gap=gap,
                            ids=used, trace=trace)
        return dict(k=None, predicted_k=pred, gap=float(c@current),
                    ids=used, trace=trace)

    def certificate(self, t, c, scope='all'):
        """Conservative finite-flip no-crossing certificate, in the paper."""
        p = self.panel
        H = self.hessian(t)
        HX = solve(H, self.X.T, assume_a='pos')
        norms = np.sqrt(np.maximum(np.sum(self.X.T*HX, axis=0), 0))
        a = float(norms.max())
        cnorm = np.sqrt(c @ solve(H, c, assume_a='pos'))
        radius = float(c@t)/cnorm
        threshold = -np.expm1(-a*radius)/a
        eligible = (p.y == 0) | (p.y == 1)
        if scope == 'incident':
            targets = np.flatnonzero(c[:p.m])
            eligible &= np.isin(p.a, targets) | np.isin(p.b, targets)
        costs = np.sort(norms[p.group[eligible]])[::-1]
        sums = np.cumsum(costs)
        residual=self.X.T@(p.count*expit(self.X@t)-p.wins)+self.ridge*t
        residual_norm=float(np.sqrt(max(0.,residual@solve(H,residual,assume_a='pos'))))
        # strict inequality, with a conservative numerical guard
        safe = int(np.sum(sums+residual_norm < threshold-1e-9))
        return dict(safe_k=safe, a=a, radius=radius, threshold=threshold,
                    residual_norm=residual_norm)

    def direct_bound(self, t, c):
        """Exact lower bound via unconstrained transfers from first to second.

        Requires pure item effects with a positive diagonal ridge, no jointly
        estimated covariates. See paper for the grounded-Laplacian proof.
        Virtual transfers may exceed recorded capacities; they are a mathematical
        relaxation, NOT fabricated observations or an empirical attack.
        """
        p=self.panel
        if p.home is not None: raise ValueError('Direct bound excludes covariates')
        first=int(np.flatnonzero(c>0)[0]);second=int(np.flatnonzero(c<0)[0])
        capacity=int(np.sum(((p.a==first)&(p.b==second)&(p.y==1)) |
                            ((p.a==second)&(p.b==first)&(p.y==0))))
        lo,hi=0,1
        def evaluate(k):
            tt=self.fit(start=t,linear=k*c)
            residual=self.X.T@(p.count*expit(self.X@tt)-p.wins)+self.ridge*tt+k*c
            # Strong convexity gives ||tt-theta_exact||_2 <= ||gradient||_2/lambda.
            error=float(np.linalg.norm(c)*np.linalg.norm(residual)/self.ridge+1e-9)
            return float(c@tt),error
        def negative(k):
            gap,error=evaluate(k)
            return gap < -error
        while not negative(hi):hi*=2
        while hi-lo>1:
            mid=(hi+lo)//2
            if negative(mid):hi=mid
            else:lo=mid
        # All k<=lo are safe; hi is first integer virtual strict crossing.
        # If a numerical near-tie appears, weaken the certificate by one edit.
        gap_lo,error_lo=evaluate(lo)
        safe=lo
        while safe>0:
            safe_gap,safe_error=evaluate(safe)
            if safe_gap>safe_error:break
            safe-=1
        lower=safe+1
        return dict(lower_k=lower,virtual_k=hi,capacity=capacity,
                    exact_by_capacity=bool(capacity>=hi and lower==hi),
                    virtual_previous_gap=gap_lo,virtual_previous_error=error_lo,
                    virtual_cross_gap=evaluate(hi)[0])


def kendall_distance(original, changed):
    pairs = np.triu_indices(len(original), 1)
    return float(np.mean((original[pairs[0]]-original[pairs[1]]) *
                         (changed[pairs[0]]-changed[pairs[1]]) < 0))
