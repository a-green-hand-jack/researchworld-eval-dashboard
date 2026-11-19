"""Exact HT variance for full closed-neighborhood exposure and additive noise.

Under one-hop exposure sufficiency, full exposure observes the corresponding
endpoint mean. All assignment units are independent Bernoulli(p); node and
cluster designs differ only in their closed-neighborhood assignment-unit sets.
Blockwise long-double accumulation avoids truncating rare-event risk.
"""
import numpy as np
from scipy import sparse
from .core import outcome_mean


def neighborhood_membership(graph, design):
    a=graph.adjacency.tocoo()
    row=np.r_[a.row,np.arange(graph.n)]
    neighbor=np.r_[a.col,np.arange(graph.n)]
    if design=="bernoulli":
        col=neighbor
        units=graph.n
    elif design=="cluster":
        col=graph.clusters[neighbor]
        units=int(graph.clusters.max()+1)
    else:
        raise ValueError(design)
    s=sparse.coo_matrix((np.ones(len(row),dtype=np.int32),(row,col)),shape=(graph.n,units)).tocsr()
    s.data[:]=1
    return s


def exact_ht_risk(graph, design, p, noise_map, mechanism="linear", gamma=1., block_size=128):
    if mechanism=="twohop":
        raise ValueError("One-hop full exposure does not identify two-hop endpoint outcomes")
    if not 0<p<1:
        raise ValueError("Strictly interior Bernoulli assignment probability required")
    s=neighborhood_membership(graph,design)
    m1=outcome_mean(graph,np.ones(graph.n),mechanism,gamma=gamma).astype(np.longdouble)
    m0=outcome_mean(graph,np.zeros(graph.n),mechanism,gamma=gamma).astype(np.longdouble)
    total=np.longdouble(0)
    for start in range(0,graph.n,block_size):
        stop=min(graph.n,start+block_size)
        k=(s[start:stop]@s.T).toarray()
        sig=(noise_map[start:stop]@noise_map.T).toarray().astype(np.longdouble)
        multiplier1=np.expm1(-np.longdouble(np.log(p))*k)
        multiplier0=np.expm1(-np.longdouble(np.log1p(-p))*k)
        v1=(m1[start:stop,None]*m1[None,:]+sig)*multiplier1
        v0=(m0[start:stop,None]*m0[None,:]+sig)*multiplier0
        cross=2*(m1[start:stop,None]*m0[None,:]+sig)*(k>0)
        total+=np.sum(v1+v0+cross,dtype=np.longdouble)
    variance=total/np.longdouble(graph.n)**2
    if variance<=0:
        raise ArithmeticError(f"Nonpositive HT variance: {variance}")
    log10=float(np.log10(variance))
    return dict(ht_exact_log10_variance=log10,
                ht_exact_variance=float(variance) if log10<np.log10(np.finfo(float).max) else np.inf,
                ht_exact_log10_rmse=log10/2,
                ht_neighborhood_max_units=int(np.asarray(s.sum(axis=1)).max()))
