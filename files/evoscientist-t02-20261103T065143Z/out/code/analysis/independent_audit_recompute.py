"""Independent deterministic audit; never modifies train.py, analyze.py or protocols.
Run: python /work/analysis/independent_audit_recompute.py
Only main-manifest runs and extension runs already present in analysis/runs.csv are audited.
Outputs audit_checks.json, audit_cells.csv, audit_endpoints.csv, audit_diagnostics.csv,
audit_sensitivity.csv, audit_primary_pairs.csv. No training or plots.
"""
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.special import gammaln
from scipy.stats import beta, norm

ROOT = Path('/work')
OUT = ROOT / 'analysis'
sys.path.insert(0, str(ROOT))
from train import make_data, build_model

torch.set_num_threads(1)
torch.set_flush_denormal(True)
manifest = json.loads((ROOT/'main_manifest.json').read_text())
reported = pd.read_csv(OUT/'runs.csv')
extension = json.loads((ROOT/'extension_manifest.json').read_text())
configs = manifest + [c for c in extension if c['out'] in set(reported.out)]
assert len(configs) == len(reported)
reported = reported.set_index('out')
stats = json.loads((OUT/'statistics.json').read_text())
checks = Counter()
errors = []
rows_by_out = {}
endpoints = []
diagnostics = []
sensitivity = []
summary_persistence_mismatch = []


def check(ok, label, context=''):
    checks[label] += 1
    if not bool(ok):
        errors.append({'check': label, 'context': str(context)})


def onset(rows, key, threshold=.99, persistence=5):
    # Different algorithm from analyze.crossing: running length, return streak onset.
    length = 0
    for i, row in enumerate(rows):
        length = length + 1 if row[key] >= threshold else 0
        if length == persistence:
            return i - persistence + 1
    return None


def wilson(k, n, level):
    z = norm.ppf((1 + level)/2)
    center = (k + z*z/2)/(n + z*z)
    radius = z/(n+z*z)*math.sqrt(k*(n-k)/n+z*z/4)
    return [max(0., center-radius), min(1., center+radius)]


def cp(k, n, level):
    alpha = 1-level
    return [0. if k == 0 else float(beta.ppf(alpha/2,k,n-k+1)),
            1. if k == n else float(beta.ppf(1-alpha/2,k+1,n-k))]


freeze = json.loads((ROOT/'protocol_freeze.json').read_text())
hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['protocol.md','main_manifest.json','train.py','analyze.py','extension_protocol.md','extension_manifest.json']}
for p, h in freeze['sha256'].items():
    check(hashes[p] == h, 'frozen_hash', p)

for c in configs:
    folder = Path(c['out'])
    rows = [json.loads(s) for s in (folder/'metrics.jsonl').read_text().splitlines()]
    s = json.loads((folder/'summary.json').read_text())
    r = reported.loc[c['out']]
    rows_by_out[c['out']] = rows
    check(s['config'] == c, 'config_matches_manifest', folder)
    check(s['source_sha256'] == hashes['train.py'], 'source_hash', folder)
    check([v['step'] for v in rows] == list(range(0,12001,25)), 'checkpoint_grid', folder)
    check(rows[0] == s['initial'] and rows[-1] == s['final'], 'summary_boundary_rows', folder)
    check(all(np.isfinite(v) for rr in rows for v in rr.values() if isinstance(v,(float,int))), 'finite_scalar_metrics', folder)
    check(all(0 <= rr[k] <= 1 for rr in rows for k in ['train_acc','val_acc']), 'accuracy_range', folder)
    check(all(rr['fourier'] is None or 0 <= rr['fourier'] <= 1+1e-12 for rr in rows), 'fourier_range', folder)
    check(all(abs(rr['norm']**2-rr['hidden_norm']**2-rr['output_norm']**2) < 1e-9*max(1,rr['norm']**2) for rr in rows), 'layer_norm_identity', folder)
    C = c['steps']-4*c['eval_every']
    im, ig = onset(rows,'train_acc'), onset(rows,'val_acc')
    tm = None if im is None else rows[im]['step']
    tg = None if ig is None else rows[ig]['step']
    um, ug = C if tm is None else tm, C if tg is None else tg
    grok = tm is not None and tg is not None and tg >= 10*max(tm,25) and rows[im]['val_acc'] <= .5
    strict = bool(grok and all(z['train_acc'] >= .99 for z in rows[im:ig+1]))
    regressions = [] if ig is None else [z['step'] for z in rows[ig:] if z['val_acc'] < .99]
    derived = dict(tM=tm,tG=tg,eventM=tm is not None,eventG=tg is not None,uM=um,uG=ug,C=C,
                   L=math.log2((ug+25)/(um+25)),delay=ug-um,grok=grok,strict_grok=strict,
                   final_train=rows[-1]['train_acc'],final_test=rows[-1]['val_acc'],best_test=max(z['val_acc'] for z in rows),
                   post_grok_regressions=len(regressions))
    for key,value in derived.items():
        check(pd.isna(r[key]) if value is None else np.isclose(r[key], value,rtol=1e-12,atol=1e-12), 'endpoint_'+key, folder)
    ep = dict(group=c['group'],seed=c['seed'],split_seed=c['split_seed'],width=c['width'],p=c['p'],out=c['out'],**derived)
    endpoints.append(ep)
    # Raw summary uses three checkpoints, deliberately not frozen primary five.
    for key, skey in [('train_acc','t_train'),('val_acc','t_val')]:
        ii = onset(rows,key,persistence=3)
        tt = None if ii is None else rows[ii]['step']
        check(s[skey] == tt,'summary_three_checkpoint_definition',folder)
    if s['t_train'] != tm or s['t_val'] != tg:
        summary_persistence_mismatch.append(dict(out=c['out'],summary_tM=s['t_train'],frozen_tM=tm,summary_tG=s['t_val'],frozen_tG=tg))
    if c['group'] == 'primary':
        for threshold in [.95,.99,.999]:
            for persistence in [3,5,9]:
                jm, jg = onset(rows,'train_acc',threshold,persistence),onset(rows,'val_acc',threshold,persistence)
                tmm = None if jm is None else rows[jm]['step']
                tgg = None if jg is None else rows[jg]['step']
                cap = c['steps']-(persistence-1)*c['eval_every']
                for delay_ratio in [3,10]:
                    gg = tmm is not None and tgg is not None and tgg >= delay_ratio*max(tmm,25) and rows[jm]['val_acc'] <= .5
                    sensitivity.append(dict(threshold=threshold,sustained=persistence,delay_ratio=delay_ratio,width=c['width'],seed=c['seed'],fit=tmm is not None,generalized=tgg is not None,grok=gg,uG=cap if tgg is None else tgg))
    # Regenerate partitions and verify final saved model by inference only.
    x,y,tr,te = make_data(c['p'],c['fraction'],c['split_seed'],c.get('operation','add'),c['split'],c.get('random_labels',False))
    check(hashlib.sha256(tr.numpy().tobytes()).hexdigest() == s['split_hash'],'split_hash',folder)
    check((len(tr),len(te)) == (s['n_train'],s['n_val']),'split_sizes',folder)
    rev = np.isin((te.numpy()%c['p'])*c['p']+te.numpy()//c['p'],tr.numpy()).mean()
    check(rev == s['reverse_overlap'],'reverse_overlap',folder)
    check(rev == 0 or c['split']=='ordered','grouped_reverse_disjoint',folder)
    state = torch.load(folder/'model.pt',map_location='cpu',weights_only=False)
    check(state['config'] == c and torch.equal(state['train_indices'],tr),'model_metadata',folder)
    w = state['state']['fc1.weight']; v = state['state']['fc2.weight']
    check(w.numel()+v.numel()==s['params']==3*c['p']*c['width'],'parameter_count',folder)
    with torch.no_grad():
        hidden = x @ w.T
        hidden = hidden.square() if c['activation']=='square' else hidden.relu()
        logits = c.get('alpha',1.)*(hidden @ v.T)
        train_acc = (logits[tr].argmax(1)==y[tr]).float().mean().item()
        test_acc = (logits[te].argmax(1)==y[te]).float().mean().item()
        check(train_acc == rows[-1]['train_acc'] and test_acc == rows[-1]['val_acc'],'final_state_accuracy',folder)
        check(np.isclose(torch.nn.functional.cross_entropy(logits[te],y[te]).item(), rows[-1]['val_loss'],rtol=1e-6,atol=1e-8),'final_state_test_loss',folder)
        total_norm = math.sqrt(w.double().square().sum().item()+v.double().square().sum().item())
        check(np.isclose(total_norm,rows[-1]['norm'],rtol=1e-7),'final_state_norm',folder)
        fourier = None
        if c.get('operation','add')=='add' and not c.get('random_labels',False):
            z=logits.double().numpy().reshape(c['p'],c['p'],c['p'])
            z=z-z.mean(axis=2,keepdims=True)
            energy=abs(np.fft.fftn(z))**2
            fourier=float(sum(energy[k,k,-k] for k in range(1,c['p']))/energy.sum())
            check(np.isclose(fourier,rows[-1]['fourier'],atol=1e-12),'final_state_fourier',folder)
        # Initial draws rebuilt, not fitted. Compare aligned initial functions below.
        initial_model=build_model(c)
        initial_logits=initial_model(x)
        check(np.isclose(initial_logits.std().item(),rows[0]['logit_std'],rtol=1e-6,atol=1e-9),'initial_function_scale',folder)
    diagnostics.append(dict(group=c['group'],seed=c['seed'],width=c['width'],p=c['p'],initial_norm=rows[0]['norm'],final_norm=rows[-1]['norm'],initial_hidden_norm=rows[0]['hidden_norm'],initial_output_norm=rows[0]['output_norm'],final_hidden_norm=rows[-1]['hidden_norm'],final_output_norm=rows[-1]['output_norm'],initial_logit_std=rows[0]['logit_std'],final_fourier=fourier,regression_count=len(regressions),first_regression=None if not regressions else regressions[0],worst_after_grok=None if ig is None else min(z['val_acc'] for z in rows[ig:]),final_train_loss=rows[-1]['train_loss'],final_test_loss=rows[-1]['val_loss'],best_test=max(z['val_acc'] for z in rows),majority_acc=r.majority_acc,reverse_lookup_acc=r.reverse_lookup_acc,reverse_overlap=rev))

edf = pd.DataFrame(endpoints)
ddf = pd.DataFrame(diagnostics)
edf.to_csv(OUT/'audit_endpoints.csv',index=False)
ddf.to_csv(OUT/'audit_diagnostics.csv',index=False)
sens=pd.DataFrame(sensitivity).groupby(['threshold','sustained','delay_ratio','width'],as_index=False).agg(fit=('fit','sum'),generalized=('generalized','sum'),grok=('grok','sum'),median_uG=('uG','median'))
sens.to_csv(OUT/'audit_sensitivity.csv',index=False)
original_sens=pd.read_csv(OUT/'sensitivity.csv')
joined=original_sens.merge(sens.query('delay_ratio==10'),on=['threshold','sustained','width'],suffixes=('_script','_audit'))
for k in ['fit','generalized','grok','median_uG']:
    check(np.array_equal(joined[k+'_script'],joined[k+'_audit']),'all_sensitivity_'+k)

# Reproduce analyze.py RNG call sequence from independently derived inputs.
rng=np.random.default_rng(20261103)

def boot(values,level=.95):
    a=np.asarray(values,float)
    b=a[rng.integers(0,len(a),(20000,len(a)))].mean(axis=1)
    return dict(mean=float(a.mean()),lo=float(np.quantile(b,(1-level)/2)),hi=float(np.quantile(b,(1+level)/2)),n=len(a))

aggregates=json.loads((OUT/'group_summary.json').read_text())
cells=[]
for (g,w),t in edf.groupby(['group','width'],sort=False):
    bci=boot(t.final_test)
    ref=next(x for x in aggregates if x['group']==g and x['width']==w)
    check(all(np.isclose(bci[k],ref['mean_final_test'][k],rtol=1e-12,atol=1e-12) for k in bci),'cell_bootstrap_exact_reproduction',(g,w))
    check([int(t.eventM.sum()),int(t.eventG.sum()),int(t.grok.sum()),int(t.strict_grok.sum())]==[ref[k] for k in ['fit','generalized','grok','strict_grok']],'cell_event_counts',(g,w))
    cells.append(dict(group=g,width=w,n=len(t),fit=int(t.eventM.sum()),generalized=int(t.eventG.sum()),grok=int(t.grok.sum()),strict_grok=int(t.strict_grok.sum()),median_fit=t.uM.median(),median_restricted_tG=t.uG.median(),final_accuracy_mean=bci['mean'],final_accuracy_ci95_lo=bci['lo'],final_accuracy_ci95_hi=bci['hi']))
pd.DataFrame(cells).to_csv(OUT/'audit_cells.csv',index=False)
a=edf.query("group=='primary' and width==64").set_index('seed').sort_index()
b=edf.query("group=='primary' and width==256").set_index('seed').sort_index()
check(a.split_seed.equals(b.split_seed),'primary_joint_block_pairing')
dM=np.log2((b.uM+25)/(a.uM+25));dG=np.log2((b.uG+25)/(a.uG+25));dL=dG-dM
pairs=pd.DataFrame(dict(seed=a.index,tM64=a.uM,tG64=a.uG,tM256=b.uM,tG256=b.uG,dL=dL,dM=dM,dG=dG))
pairs.to_csv(OUT/'audit_primary_pairs.csv',index=False)
p1_reproduced=dict(relative_clock=boot(dL),relative_clock_adjusted=boot(dL,.975),train_clock=boot(dM),generalization_clock=boot(dG))
for k,vv in p1_reproduced.items():
    check(all(np.isclose(vv[z],stats['P1'][k][z],atol=1e-12,rtol=1e-12) for z in vv),'primary_bootstrap_exact_reproduction',k)
zero=edf.query("group=='decay0' and width==256").set_index('seed').sort_index()
check(zero.split_seed.equals(b.split_seed),'decay_joint_block_pairing')
dp=b.eventG.astype(int)-zero.eventG.astype(int)
for k,level in [('paired_success_difference',.95),('paired_success_difference_adjusted',.975)]:
    ci=boot(dp,level)
    check(ci==stats['P2'][k],'P2_bootstrap_exact_reproduction',k)

# Exact empirical nonparametric bootstrap distribution for the ten paired blocks.
# Multinomial count-vector enumeration avoids Monte Carlo error (92378 vectors).
def compositions(total, parts):
    if parts==1:
        yield (total,)
    else:
        for j in range(total+1):
            for rest in compositions(total-j,parts-1):
                yield (j,)+rest

n=len(a)
counts=np.asarray(list(compositions(n,n)),dtype=np.int16)
weights=np.exp(gammaln(n+1)-gammaln(counts+1).sum(axis=1)-n*math.log(n))
check(np.isclose(weights.sum(),1,atol=1e-12),'exact_bootstrap_probability_mass')

def exact_boot(values):
    av=np.asarray(values,float)
    means=counts@av/n
    ix=np.argsort(means)
    cumulative=np.cumsum(weights[ix]); ordered=means[ix]
    def q(prob): return float(ordered[min(np.searchsorted(cumulative,prob),len(ordered)-1)])
    return dict(mean=float(av.mean()),ci95=[q(.025),q(.975)],ci975=[q(.0125),q(.9875)],geometric_factor=float(2**av.mean()))

p1_exact={key:exact_boot(vals) for key,vals in [('relative_clock',dL),('train_clock',dM),('generalization_clock',dG)]}
p2_uncertainty={}
for level in [.95,.975]:
    p2_uncertainty[str(level)] = dict(wilson_decay1=wilson(10,10,level),wilson_decay0=wilson(0,10,level),clopper_pearson_decay1=cp(10,10,level),clopper_pearson_decay0=cp(0,10,level))
    # Bonferroni marginal intervals, regardless of within-pair dependence.
    marginal_level=1-(1-level)/2
    w1,w0=wilson(10,10,marginal_level),wilson(0,10,marginal_level)
    c1,c0=cp(10,10,marginal_level),cp(0,10,marginal_level)
    p2_uncertainty[str(level)]['bonferroni_wilson_difference_envelope']=[w1[0]-w0[1],w1[1]-w0[0]]
    p2_uncertainty[str(level)]['bonferroni_exact_difference_envelope']=[c1[0]-c0[1],c1[1]-c0[0]]
    # All ten D=+1. Exact lower CP bound for q=P(D=+1), then E[D]>=2q-1.
    # This is a conservative paired bounded-mean interval valid for arbitrary paired Bernoulli dependence.
    p2_uncertainty[str(level)]['exact_paired_bounded_mean_interval']=[2*((1-level)/2)**(1/10)-1,1.]

replication=[]
for seed in range(100,110):
    ca=next(c for c in configs if c['group']=='replicated' and c['seed']==seed)
    cb=next(c for c in configs if c['group']=='rate_matched' and c['seed']==seed)
    ra,rb=rows_by_out[ca['out']],rows_by_out[cb['out']]
    dif={key:max(abs(x[key]-y[key]) for x,y in zip(ra,rb)) for key in ['train_loss','val_loss','train_acc','val_acc','fourier','logit_std']}
    epa=edf.loc[edf.out==ca['out']].iloc[0];epb=edf.loc[edf.out==cb['out']].iloc[0]
    check(epa.tM==epb.tM and epa.tG==epb.tG,'replication_clock_identity',seed)
    ref=next(v for v in stats['replication_trajectory_differences'] if v['seed']==seed)
    for key, raw in [('max_train_loss_difference','train_loss'),('max_test_loss_difference','val_loss'),('max_test_accuracy_difference','val_acc')]:
        check(dif[raw]==ref[key],'replication_difference_reproduction',(seed,key))
    with torch.no_grad():
        x,_,_,_=make_data(ca['p'],ca['fraction'],ca['split_seed'],split=ca['split'])
        f1=build_model(ca)(x);f2=build_model(cb)(x)
        initial_max=float((f1-f2).abs().max())
    replication.append(dict(seed=seed,initial_max_logit_difference=initial_max,**dif))

regressions=[dict(group=e['group'],seed=e['seed'],width=e['width'],tG=e['tG'],final_test=e['final_test'],**{k:d[k] for k in ['regression_count','first_regression','worst_after_grok']}) for e,d in zip(endpoints,diagnostics) if d['regression_count']]
extension_complete=sum((Path(c['out'])/'summary.json').exists() for c in extension)
result=dict(n_runs=len(configs),n_main=len(manifest),n_extension_in_analyzed_outputs=len(configs)-len(manifest),n_extension_complete_at_audit_end=extension_complete,
            n_checkpoint_rows=sum(map(len,rows_by_out.values())),hashes=hashes,check_counts=dict(checks),n_checks=sum(checks.values()),errors=errors,
            primary_exact_bootstrap=p1_exact,P2_uncertainty=p2_uncertainty,replication=replication,
            summary_three_vs_five_persistence_disagreements=summary_persistence_mismatch,regressions=regressions,
            environments=sorted(set(json.dumps(json.loads((Path(c['out'])/'summary.json').read_text())['environment'],sort_keys=True) for c in configs)))
(OUT/'audit_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['n_runs','n_extension_in_analyzed_outputs','n_extension_complete_at_audit_end','n_checkpoint_rows','n_checks','errors','primary_exact_bootstrap','P2_uncertainty','summary_three_vs_five_persistence_disagreements','regressions']},indent=2))
if errors:
    raise SystemExit('Independent audit checks failed; see audit_checks.json')
