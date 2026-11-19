"""Graph loading / generation, clustering. All graphs returned as symmetric binary scipy CSR (largest CC)."""
import os, numpy as np, scipy.sparse as sp, networkx as nx
from scipy.sparse.csgraph import connected_components

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA = os.path.join(ROOT, 'data')
CACHE = os.path.join(ROOT, 'results', 'cache')
os.makedirs(CACHE, exist_ok=True)


def _finish(A):
    A = sp.csr_matrix(A, dtype=np.float64)
    A = ((A + A.T) > 0).astype(np.float64)
    A.setdiag(0); A.eliminate_zeros()
    nc, lab = connected_components(A, directed=False)
    big = np.argmax(np.bincount(lab))
    keep = np.where(lab == big)[0]
    A = A[keep][:, keep].tocsr()
    return A


def from_nx(G):
    return _finish(nx.to_scipy_sparse_array(G, format='csr'))


def load_stanford3():
    p = os.path.join(DATA, 'stanford3', 'socfb-Stanford3.mtx')
    with open(p) as f:
        lines = [l for l in f if not l.startswith('%')]
    n = int(lines[0].split()[0])
    e = np.loadtxt(lines[1:], dtype=np.int64) - 1
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    return _finish(A)


def load_egofb():
    e = np.loadtxt(os.path.join(DATA, 'egofb', 'facebook_combined.txt'), dtype=np.int64)
    n = e.max() + 1
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    return _finish(A)


def sbm(n, K, d, mix, rng):
    s = n // K
    p_in = (1 - mix) * d / (s - 1)
    p_out = mix * d / (n - s)
    P = np.full((K, K), p_out); np.fill_diagonal(P, p_in)
    return nx.stochastic_block_model([s] * K, P, seed=int(rng.integers(2**31)))


def make_graph(spec, seed=0):
    """spec: string like 'er:n=3000,d=16', 'ba:n=3000,m=8', 'ws:n=3000,k=16,b=0.1',
    'sbm:n=3000,K=30,d=16,mix=0.1', 'stanford3', 'egofb'."""
    name, _, args = spec.partition(':')
    kw = {k: float(v) for k, v in (a.split('=') for a in args.split(',') if a)}
    rng = np.random.default_rng(seed)
    s = int(rng.integers(2**31))
    if name == 'stanford3': return load_stanford3()
    if name == 'egofb': return load_egofb()
    n = int(kw.get('n', 3000))
    if name == 'er': G = nx.fast_gnp_random_graph(n, kw['d'] / (n - 1), seed=s)
    elif name == 'ba': G = nx.barabasi_albert_graph(n, int(kw['m']), seed=s)
    elif name == 'ws': G = nx.watts_strogatz_graph(n, int(kw['k']), kw.get('b', 0.1), seed=s)
    elif name == 'sbm': G = sbm(n, int(kw['K']), kw['d'], kw['mix'], rng)
    else: raise ValueError(spec)
    return from_nx(G)


def louvain(A, resolution, seed=0):
    G = nx.from_scipy_sparse_array(A)
    comms = nx.community.louvain_communities(G, resolution=resolution, seed=seed)
    lab = np.zeros(A.shape[0], dtype=np.int64)
    for k, c in enumerate(comms):
        lab[list(c)] = k
    return lab


def clusters(spec, A, resolution, seed=0):
    f = os.path.join(CACHE, 'louv_%s_s%d_r%g.npy' % (spec.replace(':', '_').replace(',', '_').replace('=', ''), seed, resolution))
    if os.path.exists(f):
        lab = np.load(f)
        if len(lab) == A.shape[0]: return lab
    lab = louvain(A, resolution, seed)
    np.save(f, lab)
    return lab


def cut_fraction(A, lab):
    r, c = A.nonzero()
    return float(np.mean(lab[r] != lab[c]))


def perturb(A, frac, rng):
    """Observed graph: delete a fraction `frac` of edges and add the same number of uniformly random edges."""
    n = A.shape[0]
    U = sp.triu(A, 1).tocoo()
    m = len(U.row)
    k = int(round(frac * m))
    keep = np.ones(m, bool); keep[rng.choice(m, k, replace=False)] = False
    r = np.concatenate([U.row[keep], rng.integers(0, n, k)])
    c = np.concatenate([U.col[keep], rng.integers(0, n, k)])
    B = sp.coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)).tocsr()
    B = ((B + B.T) > 0).astype(np.float64); B.setdiag(0); B.eliminate_zeros()
    return B
