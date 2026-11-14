"""Supplemental deterministic diagnostics for independent_audit.md; no training."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from scipy.special import gammaln

P=Path('/work/analysis')
e=pd.read_csv(P/'audit_endpoints.csv')
d=pd.read_csv(P/'audit_diagnostics.csv')
cells=d.groupby(['group','width'],sort=False).mean(numeric_only=True)
cells.to_csv(P/'audit_diagnostic_cells.csv')
manifest=json.loads(Path('/work/main_manifest.json').read_text())
details=[]
for c in manifest:
    ep=e.loc[e.out==c['out']].iloc[0]
    if ep.post_grok_regressions==0:
        continue
    rows=[json.loads(x) for x in (Path(c['out'])/'metrics.jsonl').read_text().splitlines()]
    details.append(dict(group=c['group'],seed=c['seed'],width=c['width'],tM=int(ep.tM),tG=int(ep.tG),
                        min_train_between_clocks=min(r['train_acc'] for r in rows if ep.tM<=r['step']<=ep.tG),
                        peak_norm=max(r['norm'] for r in rows),
                        final_test=ep.final_test,best_test=ep.best_test,
                        below99_after_grok_steps=[r['step'] for r in rows if r['step']>=ep.tG and r['val_acc']<.99]))
(P/'audit_regression_details.json').write_text(json.dumps(details,indent=2)+'\n')
# Preserve all pre-specified P3 comparisons, no selection by outcome.
def compositions(n,k):
    if k==1:
        yield (n,)
    else:
        for i in range(n+1):
            for rest in compositions(n-i,k-1):
                yield (i,)+rest
counts=np.array(list(compositions(10,10)))
prob=np.exp(gammaln(11)-gammaln(counts+1).sum(axis=1)-10*np.log(10))
contrasts=[]
for ga,wa,gb,wb in [('primary',256,'replicated',256),('primary',64,'rate_matched',64),('primary',256,'rescale',256),('primary',32,'rescale',32)]:
    a=e.query('group==@ga and width==@wa').set_index('seed').sort_index()
    b=e.query('group==@gb and width==@wb').set_index('seed').sort_index()
    assert a.split_seed.equals(b.split_seed)
    delta=np.log2((b.uG+25)/(a.uG+25)).to_numpy()
    vals=counts@delta/10
    ix=np.argsort(vals);cumulative=np.cumsum(prob[ix])
    ci=[float(vals[ix[np.searchsorted(cumulative,q)]]) for q in [.025,.975]]
    contrasts.append(dict(reference_group=ga,reference_width=wa,comparison_group=gb,comparison_width=wb,n=10,
        mean_paired_log2_restricted_tG_difference=float(delta.mean()),ci95_lo=ci[0],ci95_hi=ci[1],
        geometric_clock_factor=float(2**delta.mean()),all_generalization_observed=bool(a.eventG.all() and b.eventG.all())))
pd.DataFrame(contrasts).to_csv(P/'audit_secondary_comparisons.csv',index=False)
# Test clone symmetry and finite-precision mapped parameter differences at final state.
torch.set_num_threads(1)
rep=[]
for seed in range(100,110):
    ca=next(c for c in manifest if c['group']=='replicated' and c['seed']==seed)
    cb=next(c for c in manifest if c['group']=='rate_matched' and c['seed']==seed)
    sa=torch.load(Path(ca['out'])/'model.pt',map_location='cpu',weights_only=False)['state']
    sb=torch.load(Path(cb['out'])/'model.pt',map_location='cpu',weights_only=False)['state']
    wa=sa['fc1.weight'].reshape(64,4,-1);va=sa['fc2.weight'].reshape(31,64,4)
    rep.append(dict(seed=seed,max_hidden_clone_difference=float((wa-wa[:,:1]).abs().max()),
        max_output_clone_difference=float((va-va[:,:,:1]).abs().max()),
        max_mapped_hidden_parameter_difference=float((wa[:,0]-sb['fc1.weight']).abs().max()),
        max_mapped_output_parameter_difference=float((4*va[:,:,0]-sb['fc2.weight']).abs().max())))
(P/'audit_final_replication_parameters.json').write_text(json.dumps(rep,indent=2)+'\n')
# Reconstruct RNG consumption with/without exploratory extension, without rerunning
# or modifying the original script and without overwriting its final outputs.
rng_order={}
main_outs={c['out'] for c in manifest}
for name, frame in [('main_only',e[e.out.isin(main_outs)]),('main_and_extension',e)]:
    rng=np.random.default_rng(20261103)
    for _, cell in frame.groupby(['group','width'],sort=False):
        rng.integers(len(cell),size=(20000,len(cell)))
    aa=frame.query("group=='primary' and width==64").set_index('seed').sort_index()
    bb=frame.query("group=='primary' and width==256").set_index('seed').sort_index()
    delta=(bb.L-aa.L).to_numpy()
    vals=delta[rng.integers(10,size=(20000,10))].mean(axis=1)
    rng_order[name]=dict(mean=float(delta.mean()),ci95=np.quantile(vals,[.025,.975]).tolist())
(P/'audit_bootstrap_rng_order.json').write_text(json.dumps(rng_order,indent=2)+'\n')
print(pd.DataFrame(contrasts).to_string(index=False))
print('max final parameter differences', {k:max(r[k] for r in rep) for k in rep[0] if k!='seed'})
print('regressions',[(r['group'],r['seed'],r['width'],r['min_train_between_clocks'],r['peak_norm']) for r in details])
