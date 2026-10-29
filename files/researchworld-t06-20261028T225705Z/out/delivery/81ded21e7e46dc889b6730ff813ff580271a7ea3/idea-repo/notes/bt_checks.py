"""Context checks for the plan: BT MLE existence, tie models, first-order (AMIP-style) influence formula.
Reads raw files from /hutian/data (not in the repo). Usage: python3 -I bt_checks.py <datadir>"""
import sys, numpy as np, pandas as pd
from scipy.optimize import minimize
from scipy.sparse.csgraph import connected_components
from scipy.sparse import coo_matrix
D = sys.argv[1]

def load():
    a = pd.read_csv(f'{D}/arena55k.csv', usecols=['model_a','model_b','winner_model_a','winner_model_b','winner_tie'])
    y = np.where(a.winner_model_a==1, 1.0, np.where(a.winner_model_b==1, 0.0, 0.5))
    arena = (a.model_a.values, a.model_b.values, y)
    h = pd.read_parquet(f'{D}/mt_human.parquet', columns=['model_a','model_b','winner'])
    yh = h.winner.map({'model_a':1.0,'model_b':0.0,'tie':0.5}).values
    mt = (h.model_a.values, h.model_b.values, yh)
    n = pd.read_csv(f'{D}/nba.csv', usecols=['year_id','_iscopy','team_id','opp_id','game_result','is_playoffs'])
    n = n[n._iscopy==0]
    nba = n
    return arena, mt, nba

def encode(a, b, y):
    names = sorted(set(a)|set(b)); ix = {m:i for i,m in enumerate(names)}
    return names, np.array([ix[m] for m in a]), np.array([ix[m] for m in b]), np.asarray(y, float)

def fit_bt(K, ia, ib, y, w=None, lam=1e-6):
    """Weighted BT logistic MLE with fractional response y (half-win ties), small L2. P(a beats b)=sigmoid(t_a - t_b)."""
    w = np.ones(len(y)) if w is None else w
    def f(t):
        d = t[ia]-t[ib]; p = 1/(1+np.exp(-d))
        ll = np.sum(w*(y*np.log(p+1e-300)+(1-y)*np.log(1-p+1e-300)))
        g = np.zeros(K); r = w*(y-p); np.add.at(g, ia, r); np.add.at(g, ib, -r)
        return -ll+0.5*lam*t@t, -g+lam*t
    r = minimize(f, np.zeros(K), jac=True, method='L-BFGS-B', options={'maxiter':5000,'gtol':1e-10,'ftol':1e-15})
    return r.x - r.x.mean()

def hessian(t, ia, ib, w, lam):
    K = len(t); p = 1/(1+np.exp(-(t[ia]-t[ib]))); v = w*p*(1-p)
    H = np.zeros((K,K))
    np.add.at(H,(ia,ia),v); np.add.at(H,(ib,ib),v); np.add.at(H,(ia,ib),-v); np.add.at(H,(ib,ia),-v)
    return H+lam*np.eye(K), p

def strong_conn(K, ia, ib, y):
    """Ford/Zermelo condition: directed graph i->j if i beat j (ties = both ways) strongly connected."""
    src = list(ia[y>=0.5])+list(ib[y<=0.5]); dst = list(ib[y>=0.5])+list(ia[y<=0.5])
    G = coo_matrix((np.ones(len(src)),(src,dst)),shape=(K,K))
    nc, _ = connected_components(G, directed=True, connection='strong')
    return nc

def tie_models(K, ia, ib, y):
    """Compare half-win with Davidson (nu fitted) and Rao-Kupper (theta fitted); return Spearman between scores."""
    win = (y==1.0).astype(float); lose = (y==0.0).astype(float); tie = (y==0.5).astype(float)
    def nll_dav(x):
        t = x[:K]; nu = np.exp(x[K]); d = t[ia]-t[ib]
        # P(a)=e^{d/2}/den, P(b)=e^{-d/2}/den, P(tie)=nu/den with den=e^{d/2}+e^{-d/2}+nu
        den = np.logaddexp(np.logaddexp(d/2,-d/2), np.log(nu))
        ll = win*(d/2-den)+lose*(-d/2-den)+tie*(np.log(nu)-den)
        return -ll.sum()+0.5e-6*t@t
    def nll_rk(x):
        t = x[:K]; th = 1+np.exp(x[K]); d = t[ia]-t[ib]
        lpa = d-np.logaddexp(d, np.log(th)); lpb = -np.logaddexp(np.log(th)+d, 0)
        pa, pb = np.exp(lpa), np.exp(lpb); pt = np.clip(1-pa-pb,1e-300,1)
        return -(win*lpa+lose*lpb+tie*np.log(pt)).sum()+0.5e-6*t@t
    out = {}
    for nm, fn in [('davidson',nll_dav),('rao_kupper',nll_rk)]:
        r = minimize(fn, np.zeros(K+1), method='L-BFGS-B', options={'maxiter':3000,'maxfun':10**6})
        out[nm] = (r.x[:K]-r.x[:K].mean(), r.x[K], r.fun)
    return out

if __name__ == '__main__':
    from scipy.stats import spearmanr, kendalltau
    arena, mt, nba = load()
    for nm, data in [('arena55k',arena),('mtbench_human',mt)]:
        names, ia, ib, y = encode(*data); K = len(names)
        print(f'== {nm}: K={K} N={len(y)} tie_share={np.mean(y==0.5):.3f} strong components(half-win)={strong_conn(K,ia,ib,y)}'
              f' ; ties dropped: {strong_conn(K,ia[y!=.5],ib[y!=.5],y[y!=.5])}')
        wins = np.bincount(ia[y==1],minlength=K)+np.bincount(ib[y==0],minlength=K)
        loss = np.bincount(ia[y==0],minlength=K)+np.bincount(ib[y==1],minlength=K)
        print('   min wins/losses per participant:', wins.min(), loss.min())
        t_hw = fit_bt(K,ia,ib,y)
        t_drop = np.full(K,np.nan); m = y!=.5
        t_drop = fit_bt(K,ia[m],ib[m],y[m])
        tm = tie_models(K,ia,ib,y)
        print('   Spearman/Kendall half-win vs ties-dropped: %.4f / %.4f' % (spearmanr(t_hw,t_drop)[0], kendalltau(t_hw,t_drop)[0]))
        for k,(t,par,fv) in tm.items():
            print(f'   {k}: param={"nu=%.3f"%np.exp(par) if k=="davidson" else "theta=%.3f"%(1+np.exp(par))}  Spearman/Kendall vs half-win: %.4f / %.4f ; scale ratio sd(t)/sd(half-win)=%.3f' % (spearmanr(t_hw,t)[0], kendalltau(t_hw,t)[0], t.std()/t_hw.std()))
        order = np.argsort(-t_hw); print('   top5 half-win:', [(names[i], round(t_hw[i],3)) for i in order[:5]])
    # NBA: per-season connectivity (franchise-level team_id, regular season + playoffs together)
    n = nba; res = []
    for yr, g in n.groupby('year_id'):
        names, ia, ib, y = encode(g.team_id.values, g.opp_id.values, (g.game_result=='W').astype(float).values)
        res.append((yr, len(names), len(y), strong_conn(len(names),ia,ib,y)))
    r = pd.DataFrame(res, columns=['year','K','N','strong_comps'])
    print('== NBA per season: seasons', len(r), 'K median', r.K.median(), 'N median', r.N.median(), 'seasons with strong_comps>1:', (r.strong_comps>1).sum())
    print(r[r.strong_comps>1].to_string())
