import numpy as np, scipy.sparse as sp, networkx as nx, scipy.io, os
D='/work/data'; CACHE='/work/results/cache'; os.makedirs(CACHE,exist_ok=True)

def lcc(A):
    n,lab=sp.csgraph.connected_components(A,directed=False)
    big=np.argmax(np.bincount(lab)); idx=np.where(lab==big)[0]
    return A[idx][:,idx].tocsr()

def communities(A,name,seed=0):
    f=f'{CACHE}/comm_{name}.npy'
    if os.path.exists(f): return np.load(f)
    G=nx.from_scipy_sparse_array(A)
    cs=nx.community.louvain_communities(G,seed=seed)
    lab=np.zeros(A.shape[0],int)
    for k,c in enumerate(cs): lab[list(c)]=k
    np.save(f,lab); return lab

def make_graph(spec,seed=1):
    """returns (A csr, planted/louvain labels). spec: dict(kind=..., n=..., ...)"""
    k=spec['kind']; n=spec.get('n',5000)
    if k=='sbm':
        nb=spec.get('blocks',50); d=spec.get('deg',20); rho=spec.get('rho',0.1) # rho=out-block edge share
        sz=n//nb; n=sz*nb; lab=np.repeat(np.arange(nb),sz)
        pin=d*(1-rho)/(sz-1); pout=d*rho/(n-sz)
        rng=np.random.default_rng(seed)
        G=nx.stochastic_block_model([sz]*nb,[[pin if i==j else pout for j in range(nb)] for i in range(nb)],seed=seed) if n<=6000 else None
        A=nx.to_scipy_sparse_array(G,format='csr'); A=A.astype(float)
        return A,lab   # not LCC-restricted (isolated nodes handled by caller)
    if k=='ba': G=nx.barabasi_albert_graph(n,spec.get('m',8),seed=seed)
    elif k=='ws': G=nx.watts_strogatz_graph(n,spec.get('deg',20),0.1,seed=seed)
    elif k=='stanford':
        A=scipy.io.mmread(f'{D}/socfb-Stanford3.mtx').tocsr().astype(float); A=lcc(A); A.data[:]=1
        return A,communities(A,'stanford')
    elif k=='egofb':
        import gzip
        E=np.loadtxt(f'{D}/facebook_combined.txt.gz',dtype=int)
        m=E.max()+1; A=sp.coo_matrix((np.ones(len(E)),(E[:,0],E[:,1])),shape=(m,m)).tocsr(); A=((A+A.T)>0).astype(float)
        A=lcc(A); return A,communities(A,'egofb')
    A=nx.to_scipy_sparse_array(G,format='csr').astype(float)
    return A,_comm_syn(A,spec,seed)

def _comm_syn(A,spec,seed):
    name='_'.join(f'{k}{v}' for k,v in sorted(spec.items()))+f'_s{seed}'
    return communities(A,name)

# ---- outcome models: g(x,c) interference term; x=treated-neighbour fraction, c=count/dbar
def sig(u): return 1/(1+np.exp(-u))
def outcome_terms(model,z,x,c,tau,gam):
    if model=='linfrac': return tau*z+gam*x
    if model=='lincount': return tau*z+gam*c
    if model=='quad': return tau*z+gam*x**2
    if model=='sigmoid': return tau*z+gam*(sig(12*(x-0.5))-sig(-6))/(sig(6)-sig(-6))
    if model=='inter': return tau*z+gam*x+gam*z*x
    raise ValueError(model)

# ---- regression feature maps phi(z,x,c,ld) -> n x p
def phi(name,z,x,c,ld):
    o=np.ones_like(z)
    if name=='ols_frac': return np.c_[o,z,x]
    if name=='ols_count': return np.c_[o,z,c]
    if name=='ols_rich': return np.c_[o,z,x,c,z*x,ld]
    if name=='poly': return np.c_[o,z,x,x**2,z*x,ld]
    raise ValueError(name)
OLS=['ols_frac','ols_count','ols_rich','poly']

