"""Experiment definitions. Usage: python experiments.py <name> [R]"""
import sys, copy
from gate.sim import run_experiment
from gate.core import MECHS, ALL_EST

# cluster resolution used per graph (chosen so that K is moderate; see paper appendix)
CRES = {'er:n=3000,d=16': 3, 'ba:n=3000,m=8': 3, 'ws:n=3000,k=16,b=0.1': 3, 'sbm:n=3000,K=30,d=16,mix=0.1': 1,
        'egofb': 3, 'stanford3': 3}
BERN = {'kind': 'bern', 'p': 0.5}
def CL(graph, p=0.5): return {'kind': 'cluster', 'p': p, 'res': CRES.get(graph, 1)}


def e0_smoke():
    g = 'sbm:n=3000,K=30,d=16,mix=0.1'
    return [dict(exp='e0', graph=g, mech=m, design=d) for m in ['linfrac', 'sat'] for d in (BERN, CL(g))], 20


def e1_var():          # variance validation (well specified), degree and n sweeps
    cfgs = []
    for cs in [0.0, 0.5]:
      for d in [4, 8, 16, 32, 64, 128]:
        cfgs.append(dict(exp='e1', sweep='deg', comm_sd=cs, graph=f'er:n=3000,d={d}', mech='linfrac', design=BERN,
                         est=['DM', 'OLS-x', 'OLS-xd', 'OLS-cd', 'OLS-oracle']))
      for n in [500, 1000, 2000, 4000, 8000, 16000]:
        cfgs.append(dict(exp='e1', sweep='n', comm_sd=cs, graph=f'er:n={n},d=16', mech='linfrac', design=BERN,
                         est=['DM', 'OLS-x', 'OLS-xd', 'OLS-cd', 'OLS-oracle']))
    return cfgs, 300


def e2_main():
    cfgs = []
    for g in CRES:
        for m in MECHS:
            for d in (BERN, CL(g)):
                cfgs.append(dict(exp='e2', graph=g, mech=m, design=d))
    return cfgs, 200


def e3_design():
    g0 = 'sbm:n=3000,K=30,d=16,mix={}'
    cfgs = []
    for mix in [0.02, 0.1, 0.3, 0.6]:
        g = g0.format(mix)
        for m in ['linfrac', 'sat', 'thresh', 'quad', 'hetero', 'twohop']:
            for d in [{'kind': 'bern', 'p': 0.5}, {'kind': 'bern', 'p': 0.2}, {'kind': 'cluster', 'p': 0.5, 'res': 1},
                      {'kind': 'sat', 'res': 1}]:
                cfgs.append(dict(exp='e3', graph=g, mech=m, design=d,
                                 est=['DM', 'OLS-x', 'OLS-quad', 'OLS-rich', 'OLS-oracle', 'GBDT', 'Hajek']))
    return cfgs, 200


def e4_scale():
    cfgs = []
    for n in [1000, 2000, 4000, 8000, 16000]:
        g = f'sbm:n={n},K={n//100},d=16,mix=0.1'
        for m in ['linfrac', 'sat', 'thresh']:
            for d in [BERN, {'kind': 'cluster', 'p': 0.5, 'res': 1}]:
                cfgs.append(dict(exp='e4', graph=g, mech=m, design=d, est=['DM', 'OLS-x', 'OLS-quad', 'OLS-oracle', 'GBDT']))
    return cfgs, 100


def e5_dosenoise():
    cfgs = []
    g = 'sbm:n=3000,K=30,d=16,mix=0.1'
    for m in ['linfrac', 'sat']:
        for gam in [0.0, 0.5, 1.0, 2.0, 4.0]:
            for sig in [0.5, 1.0, 2.0]:
                for d in [BERN, {'kind': 'cluster', 'p': 0.5, 'res': 1}]:
                    cfgs.append(dict(exp='e5', graph=g, mech=m, gamma=gam, sigma=sig, design=d,
                                     est=['DM', 'OLS-x', 'OLS-oracle', 'GBDT']))
    return cfgs, 200


def e6_degree():
    cfgs = []
    for dd in [4, 8, 16, 32, 64, 128]:
        g = f'sbm:n=3000,K=15,d={dd},mix=0.1'
        for m in ['sat', 'thresh', 'quad', 'linfrac']:
            for d in [BERN, {'kind': 'cluster', 'p': 0.5, 'res': 1}, {'kind': 'sat', 'res': 1}]:
                cfgs.append(dict(exp='e6', graph=g, mech=m, design=d,
                                 est=['DM', 'OLS-x', 'OLS-quad', 'OLS-oracle', 'GBDT']))
    return cfgs, 200


def e7_infer():
    cfgs = []
    for g in ['er:n=3000,d=16', 'sbm:n=3000,K=30,d=16,mix=0.1']:
        for m in ['linfrac', 'sat', 'hetero', 'peer']:
            for d in [BERN, CL(g)]:
                cfgs.append(dict(exp='e7', graph=g, mech=m, design=d, infer=True, est=['DM', 'OLS-x']))
    return cfgs, 500


def e8_misspec_graph():
    cfgs = []
    g = 'sbm:n=3000,K=30,d=16,mix=0.1'
    for m in ['linfrac', 'twohop', 'sat']:
        for r in [0.0, 0.1, 0.25, 0.5, 0.75]:
            for d in [BERN, {'kind': 'cluster', 'p': 0.5, 'res': 1}]:
                cfgs.append(dict(exp='e8', graph=g, mech=m, obs_noise=r, design=d,
                                 est=['DM', 'OLS-x', 'OLS-xd', 'OLS-x2', 'OLS-oracle']))
    return cfgs, 200


def e9_prob():
    cfgs = []
    for g in ['sbm:n=3000,K=30,d=16,mix=0.1', 'er:n=3000,d=16']:
        for m in ['linfrac', 'sat', 'thresh']:
            for p in [0.05, 0.1, 0.2, 0.3, 0.5]:
                cfgs.append(dict(exp='e9', graph=g, mech=m, design={'kind': 'bern', 'p': p},
                                 est=['DM', 'OLS-x', 'OLS-quad', 'OLS-oracle', 'GBDT', 'Hajek']))
    return cfgs, 200


def e10_clusterres():
    cfgs = []
    for g, rs in [('egofb', [1, 3, 10, 30]), ('ws:n=3000,k=16,b=0.1', [1, 3, 10, 30]), ('stanford3', [1, 3, 10]),
                  ('sbm:n=3000,K=30,d=16,mix=0.3', [1, 3, 30])]:
        for r in rs:
            for m in ['linfrac', 'sat', 'thresh']:
                cfgs.append(dict(exp='e10', graph=g, mech=m, design={'kind': 'cluster', 'p': 0.5, 'res': r},
                                 est=['DM', 'OLS-x', 'OLS-quad', 'OLS-oracle', 'GBDT', 'Hajek']))
    return cfgs, 200


def e11_homophily():
    cfgs = []
    for g in ['sbm:n=3000,K=30,d=16,mix=0.1', 'egofb', 'ws:n=3000,k=16,b=0.1']:
        for cs in [0.0, 0.5, 1.0, 2.0]:
            for m in ['linfrac', 'sat']:
                for d in [BERN, CL(g) if g != 'sbm:n=3000,K=30,d=16,mix=0.1' else {'kind': 'cluster', 'p': 0.5, 'res': 1}]:
                    cfgs.append(dict(exp='e11', graph=g, mech=m, comm_sd=cs, design=d, est=['DM', 'OLS-x', 'OLS-xd', 'OLS-oracle']))
    return cfgs, 300


if __name__ == '__main__':
    name = sys.argv[1]
    cfgs, R = globals()[name]()
    if len(sys.argv) > 2: R = int(sys.argv[2])
    run_experiment(name, cfgs, R)
