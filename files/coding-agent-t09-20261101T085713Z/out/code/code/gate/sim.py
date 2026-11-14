"""Monte-Carlo engine: one 'config' = fixed population + design + noise; R replicates; parallel over blocks."""
import os, sys, zlib, json, time, itertools, numpy as np, pandas as pd
from multiprocessing import Pool
from . import graphs as G
from .core import Pop, Design, Estimators, ALL_EST

_CACHE = {}


def cfg_id(cfg):
    return zlib.crc32(json.dumps(cfg, sort_keys=True).encode())


def build(cfg):
    key = cfg_id(cfg)
    if key in _CACHE: return _CACHE[key]
    if len(_CACHE) > 3: _CACHE.clear()
    pop = Pop(cfg['graph'], cfg['mech'], gamma=cfg.get('gamma', 1.0), tau_d=cfg.get('tau_d', 1.0),
              seed=cfg.get('pop_seed', 0), obs_noise_graph=cfg.get('obs_noise', 0.0), comm_sd=cfg.get('comm_sd', 0.5))
    d = cfg['design']
    labels = None
    if d['kind'] in ('cluster', 'sat') or cfg.get('infer'):
        labels = G.clusters(cfg['graph'], pop.A, d.get('res', 1.0), cfg.get('pop_seed', 0))
    des = Design(d['kind'], d.get('p', 0.5), labels)
    est = Estimators(pop, des, which=cfg.get('est', ALL_EST), rng=np.random.default_rng([cfg_id(cfg), 999]),
                     infer_labels=labels, do_infer=bool(cfg.get('infer')))
    _CACHE[key] = (pop, des, est)
    return _CACHE[key]


_CUT = {}
def _cut(cid, pop, des):
    if des.labels is None: return np.nan
    if cid not in _CUT: _CUT[cid] = G.cut_fraction(pop.A, des.labels)
    return _CUT[cid]


def run_block(args):
    cfg, r0, r1, base_seed = args
    pop, des, est = build(cfg)
    sigma = cfg.get('sigma', 1.0)
    rows = []
    cid = cfg_id(cfg)
    for r in range(r0, r1):
        rng = np.random.default_rng([base_seed, cid, r])
        z = des.draw(pop.n, rng)
        mu = pop.mu(z)
        y = mu + sigma * rng.normal(size=pop.n)
        o = est.run(z, y, rng_seed=r)
        oS = est.run(z, mu, rng_seed=r)
        for k, v in o.items():
            row = {'cid': cid, 'rep': r, 'est': k, 'tau_hat': v['tau'], 'tau_S': oS[k]['tau']}
            for kk in ('w2', 'w1', 'wneg', 'se_hc0', 'se_hc3', 'se_cl', 'se_iid', 'n1', 'n0'):
                if kk in v: row[kk] = v[kk]
            row['frac_treated'] = float(z.mean()); row['tau'] = pop.tau; row['n'] = pop.n; row['dbar'] = pop.dbar
            row['K'] = int(des.K) if des.labels is not None else 0
            row['cut'] = _cut(cid, pop, des)
            rows.append(row)
    return rows


def flat(cfg):
    out = {}
    for k, v in cfg.items():
        if isinstance(v, dict):
            for kk, vv in v.items(): out[k + '_' + kk] = vv
        elif k != 'est': out[k] = v
    return out


def run_experiment(name, cfgs, R, block=25, base_seed=2026, procs=int(os.environ.get("NPROC", 4)), outdir=None):
    outdir = outdir or os.path.join(G.ROOT, 'results')
    tasks = [(c, r0, min(r0 + block, R), base_seed) for c in cfgs for r0 in range(0, R, block)]
    # shuffle tasks lightly so that heavy graphs interleave; keep same-config blocks adjacent for cache reuse
    t0 = time.time(); rows = []
    with Pool(procs) as pool:
        for i, rr in enumerate(pool.imap_unordered(run_block, tasks, chunksize=1)):
            rows.extend(rr)
            if i % 50 == 0: print(f'[{name}] {i}/{len(tasks)} blocks {time.time()-t0:.0f}s', flush=True)
    df = pd.DataFrame(rows)
    meta = pd.DataFrame([dict(flat(c), cid=cfg_id(c)) for c in cfgs])
    # true tau per config
    df = df.merge(meta, on='cid')
    df.to_csv(os.path.join(outdir, f'{name}.csv.gz'), index=False)
    print(f'[{name}] done {len(df)} rows, {time.time()-t0:.0f}s', flush=True)
    return df
