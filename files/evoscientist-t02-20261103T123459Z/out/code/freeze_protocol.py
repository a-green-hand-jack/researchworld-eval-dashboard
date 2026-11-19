"""Freeze the confirmatory job ledger BEFORE running any seeds 0--7.
This writes protocol.json and confirm_jobs.json once; do not rerun to amend results.
"""
import datetime
import hashlib
import json
from pathlib import Path


def build():
    jobs=[]
    base=dict(p=31,fraction=.7,steps=20000,eval_every=50,lr=.01,decay=.1,
              threads=1,task='add',normalization='sqrt',checkpoint=True,out='results/confirm')
    def add(tag,widths,**changes):
        for width in widths:
            for seed in range(8):
                jobs.append(dict(base,**dict(changes,tag=tag,width=width,seed=seed)))
    add('main',[8,16,32,64,128,256])
    for wd in [0,.05,.2]: add('decay',[32,128],decay=wd)
    add('frozen',[32,128],frozen=True)
    add('shuffle',[32,128],shuffle=True)
    add('mean',[32,128],normalization='mean')
    add('matched',[32,128],normalization='matched_mean')
    add('modulus',[32,128],p=23)
    add('subtract',[32,128],task='subtract')
    add('lowdata',[32,128],fraction=.3)
    add('middata',[32,128],fraction=.5)
    add('capacitytrain',[1024])
    add('capacityfrozen',[1024],frozen=True)
    ledger=json.dumps(jobs,indent=2)
    protocol=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='frozen before first confirmatory seed',
        train_sha256=hashlib.sha256(Path('train.py').read_bytes()).hexdigest(),
        ledger_sha256=hashlib.sha256(ledger.encode()).hexdigest(),n_runs=len(jobs),
        pilot_selection='13 independent exploratory runs, seeds900-903. Initial .3 failed; .5/.7 and .1/1 decay explored. .7/.1 selected for delayed generalization at both32 and128;32 remains partly censored in independent validation. All pilots retained.',
        population='joint split+initialization seeds0-7, paired membership across width/arm, no separate estimate of each variance component',
        hypothesis_W='h128 accelerates interpolation more than held-out rule acquisition relative to h32; D below zero, practical margin -log(1.25). Negative train contrast also required.',
        hypothesis_C='total generalization time collapses under C=t*(-log(1-lr*decay)) at half/double decay, within25percent when uncensored; common-clock restricted-time mean difference magnitude<=.15 horizon.',
        hypothesis_F='frozen and shuffled controls may interpolate but do not reach sustained99percent clean held-out accuracy; underfit frozen arms alone cannot establish this claim',
        thresholds=[.99,.95,.90],persistence=3,eval_every=50,steps=20000,
        censor_onset=19900,
        primary_contrasts=['W: [Ytrain128-Ytrain32]-[Yeval128-Yeval32], Y=log(1+min(T,19900)/50)',
                           'C32: double-minus-half normalized restricted common-clock event time',
                           'C128: same'],
        statistics='paired seed-cluster bootstrap, 10000 resamples seed20261103; exact two-sided mean signflip 256 assignments; Holm family of3; unadjusted95percent CIs and Wilson incidence intervals; no seed filtering',
        clock_method='Common grid deltaC=r(.2)*50, points<=r(.05)*20000. Next recorded evaluation at/after grid; three consecutive common-grid accuracies>=.99, first onset. Cap onset two bins before final point; compare min(onset,kappa)/kappa. Previous-evaluation sensitivity and fixed landmark5000 secondary.',
        secondaries='remaining widths, thresholds, absolute energies, controls, modulus23, subtraction, data fractions. No new confirmatory tests or settings based on outcomes.',
        pilot_gate='Four validation runs: train times100-200; h128 eval1400,1650; h32 eval15200 and censored; enough to test finite-budget hypothesis; not all events expected.',
        budget='240 runs at20000 updates; ~few CPU-hours projected from pilot1-2ms/update; 8workers,1thread each; high-width capacity controls slower. Fixed horizon, no slow-arm extensions.',
        scope='quadratic activation,3ph params,AdamW,synthetic pair split. Not first model-wise grokking,not universal law,not transformer reproduction.')
    for f in ['confirm_jobs.json','protocol.json']:
        if Path(f).exists(): raise RuntimeError('protocol exists: refusing overwrite')
    Path('confirm_jobs.json').write_text(ledger)
    Path('protocol.json').write_text(json.dumps(protocol,indent=2))
    print(json.dumps(protocol,indent=2))

if __name__=='__main__':build()
