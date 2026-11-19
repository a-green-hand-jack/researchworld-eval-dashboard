"""Construct the settled complete 204-run matrix without observing outcomes."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
base = dict(p=31,fraction=.5,task='add',activation='relu',lr=.001,weight_decay=1.,
    steps=60200,onset_horizon=60000,eval_every=100,report_every=10000,checkpoint_every=10000,
    threads=1,betas=[.9,.999],eps=1e-8,split_rule='ordered',frozen_hidden=False)
runs = []
for family,blocks,widths,changes in [
    ('main',12,[32,64,128,256,512],{}),
    ('decay',8,[32,128,512],dict(weight_decay=.1)),
    ('frozen',8,[32,128,512],dict(frozen_hidden=True)),
    ('lr-low',8,[32,128,512],dict(lr=.0003)),
    ('lr-high',8,[32,128,512],dict(lr=.003)),
    ('orbit',8,[32,128,512],dict(split_rule='orbit')),
    ('multiply',8,[32,128,512],dict(task='multiply'))]:
    for block in range(blocks):
        for width in widths:
            runs.append(dict(base,**changes,name=f'{family}_w{width:03d}_b{block:02d}',family=family,
                block=block,width=width,split_seed=1100+block,init_seed=2100+block,
                stage='main-and-frozen' if family in ['main','frozen'] else 'follow-on'))
assert len(runs)==204 and len({r['name'] for r in runs})==204
assert all(r['split_seed']!=100 and r['init_seed']!=200 for r in runs)
# A fixed greedy width-weight schedule distributes independent runs; it does not use outcomes.
for stage in ['main-and-frozen','follow-on']:
    jobs = [[],[]]
    costs = [0,0]
    for run in sorted([r for r in runs if r['stage']==stage],key=lambda r:(-r['width'],r['name'])):
        index = min(range(2),key=lambda j:costs[j])
        jobs[index].append(run)
        costs[index]+=run['width']
    for index,job in enumerate(jobs):
        destination = root/'configs'/'stages'/f'{stage}-{index+1}.json'
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(job,indent=2)+'\n')
manifest = dict(schema_version=1,status='registered before fresh outcomes; production requires gates',
    source_protocol='story-repo plan/protocol.md, settled 2026-11-03',
    total_runs=len(runs),seed_blocks='j=0..11 main; j=0..7 secondary, split=1100+j, init=2100+j',
    runs=runs)
(root/'configs'/'confirmatory.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Registered {len(runs)} runs')
