"""Analysis-only provenance for findings.md; never imports/runs experiment code.
Run: python /work/analysis/findings_calculations.py
Reads frozen results; writes only findings_evidence/* and this script is separate
from the experiment implementation. All intervals are descriptive, not tests.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path('/work')
OUT = ROOT / 'analysis/findings_evidence'
OUT.mkdir(exist_ok=True)
inputs = [ROOT/'plan.md', *[ROOT/'analysis'/s for s in [
    'cell_summary.csv','instance_metrics.csv','gap_summary.csv',
    'background_metrics.csv','timing_summary.csv','library_summary.csv',
    'reference_diagnostics.csv','resource_summary.json','run_metrics.csv.gz',
    'library_raw.csv','timing_raw.csv']],
    *[ROOT/'artifacts'/s for s in ['data_extra_audit.json',
    'library_numerics_diagnosis.md','source_notes.md','data_manifest.json']],
    ROOT/'analyze_results.py', ROOT/'shap_audit.py', ROOT/'diagnostics.py',
    ROOT/'run_experiments.py', ROOT/'results/reference_escalation_rule.json']
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
hashes = {str(p): sha(p) for p in inputs}
c = pd.read_csv(ROOT/'analysis/cell_summary.csv')
i = pd.read_csv(ROOT/'analysis/instance_metrics.csv')
g = pd.read_csv(ROOT/'analysis/gap_summary.csv')
b = pd.read_csv(ROOT/'analysis/background_metrics.csv')
r = pd.read_csv(ROOT/'analysis/reference_diagnostics.csv')
u = pd.read_csv(ROOT/'analysis/run_metrics.csv.gz')
t = pd.read_csv(ROOT/'analysis/timing_summary.csv')
l = pd.read_csv(ROOT/'analysis/library_raw.csv')
tr = pd.read_csv(ROOT/'analysis/timing_raw.csv')
assert len(c)==54 and len(i)==3888 and len(r)==648 and len(u)==248832
keys=['dataset','model','seed','slot','method','p']
assert not i.duplicated(keys).any()
assert (u.groupby(keys).size()==64).all()
assert (i.groupby(['dataset','model','method','p']).size()==72).all()
assert not u[['success','top3','top1','error','signok','regret']].isna().any().any()
assert np.allclose(c.success*4608,np.round(c.success*4608))
# Supplemental raw reference-scale quantities, without recomputing scores.
rawrows=[]
for rec in r.itertuples(index=False):
    p=ROOT/'results/main'/f'{rec.dataset}_{rec.model}_{rec.seed}_{rec.slot:02d}.npz'
    hashes[str(p)]=sha(p)
    with np.load(p,allow_pickle=False) as a:
        v=a['reference']; sv=np.sort(np.abs(v)); mass=float(sv[-3:].sum())
        rr=dict(dataset=rec.dataset,model=rec.model,seed=rec.seed,slot=rec.slot,
                reference_top3_mass=mass,raw_gap=float(sv[-3]-sv[-4]),
                efficiency_max=float(a['efficiency_max']),
                audit_pairs=int(len(a['pairs_audit'])) if 'pairs_audit' in a else 0,
                split_sign=bool(a['split_sign']))
        rawrows.append(rr)
raw=pd.DataFrame(rawrows)
raw.to_csv(OUT/'reference_scale.csv',index=False)
i=i.merge(raw,on=['dataset','model','seed','slot'],validate='many_to_one')
i['absolute_l1_mean']=i.error*np.maximum(i.norm,.02)
i['absolute_regret_mean']=i.regret*np.maximum(i.reference_top3_mass,.02)
u['error_pass']=u.error<=.2
rp=u.groupby(keys).agg(error_pass=('error_pass','mean')).reset_index()
i=i.merge(rp,on=keys,validate='one_to_one')
components=i.groupby(['dataset','model','method','p']).agg(
    n=('point','size'),error_pass=('error_pass','mean'),
    absolute_l1_mean=('absolute_l1_mean','mean'),
    absolute_regret_mean=('absolute_regret_mean','mean'),
    zero_agree_points=('agree',lambda x:int((x==0).sum()))).reset_index()
ct=c.merge(components,on=['dataset','model','method','p','n'],validate='one_to_one')
ct['success_count']=np.rint(ct.success*4608).astype(int)
ct['runs']=4608
ct.to_csv(OUT/'cell_evidence.csv',index=False)
# Same-point, seed-stratified descriptive bootstrap contrasts, no p-values.
contrasts=[]
for (ds,mo),dd in i.groupby(['dataset','model']):
    w=dd.pivot(index=['seed','slot'],columns=['method','p'],values='success').sort_index()
    rng=np.random.default_rng(20261111)
    ix=np.concatenate([rng.choice(np.flatnonzero(w.index.get_level_values('seed')==s),
        size=(2000,24),replace=True) for s in [11,29,47]],axis=1)
    compare=[('perm-minus-kernel',p,('perm',p),('kernel',p)) for p in [1,4,16]]
    compare += [(m+'-P16-minus-P1',16,(m,16),(m,1)) for m in ['kernel','perm']]
    for label,p,aa,bb in compare:
        d=(w[aa]-w[bb]).to_numpy(); lo,hi=np.quantile(d[ix].mean(axis=1),[.025,.975])
        contrasts.append(dict(dataset=ds,model=mo,contrast=label,p=p,
                              difference=d.mean(),lo=lo,hi=hi,n=72))
pd.DataFrame(contrasts).to_csv(OUT/'paired_success_contrasts.csv',index=False)
# Gap strata kept separate by dataset/model/method/budget; retain empty strata.
gapextra=i.groupby(['dataset','model','method','p','gap_stratum']).agg(
    raw_gap_min=('raw_gap','min'),raw_gap_max=('raw_gap','max'),
    absolute_regret_mean=('absolute_regret_mean','mean'),
    normalized_regret_max_instance_mean=('regret','max'),
    absolute_l1_mean=('absolute_l1_mean','mean')).reset_index().rename(columns={'gap_stratum':'stratum'})
g.merge(gapextra,on=['dataset','model','method','p','stratum'],how='left',validate='one_to_one').to_csv(OUT/'gap_evidence.csv',index=False)
# Eight fixed seed-11 points per dataset/model. One shared nested background per B.
bg=b.groupby(['dataset','model','b','method','p']).agg(
    n=('slot','size'),success=('success','mean'),error=('error','mean')).reset_index()
bg.to_csv(OUT/'background_own_game.csv',index=False)
drift=b[['dataset','model','slot','b','drift']].drop_duplicates()
assert len(drift)==144
bd=drift.groupby(['dataset','model','b']).agg(n=('slot','size'),mean=('drift','mean'),
    median=('drift','median'),minimum=('drift','min'),maximum=('drift','max')).reset_index()
bd.to_csv(OUT/'background_drift.csv',index=False)
# Main references and all-pair counts are not independent replicates.
refsum=r[r.dataset=='german'].groupby('model').agg(
    n=('qualified','size'),qualified=('qualified','sum'),initial_qualified=('initial_qualified','sum'),
    escalated=('escalated','sum'),split_error_max=('split_error','max'),split_max_max=('split_max','max'),
    audit_n=('audit_error','count'),audit_error_max=('audit_error','max'),
    reference_boot_coordinate_width_max=('ref_boot_max_coordinate_width','max'))
refsum.to_csv(OUT/'german_reference_summary.csv')
refdiscord=i[i.dataset=='german'].groupby(['model','method','p']).agg(
    points_discordant=('ref_label_discord',lambda v:int((v>0).sum())),
    disagree_rate=('ref_label_discord','mean')).reset_index()
refdiscord['disagree_runs']=np.rint(refdiscord.disagree_rate*4608).astype(int)
refdiscord.to_csv(OUT/'german_label_sensitivity.csv',index=False)
# Re-evaluate only the frozen primary label for the six existing reference audits.
# This is a sensitivity calculation from saved vectors, not a new estimator.
def primary_labels(est, ref):
    order=np.argsort(-np.round(np.abs(est),12),axis=1,kind='stable')[:,:3]
    rt=np.argsort(-np.round(np.abs(ref),12),kind='stable')[:3]
    tops=(np.sort(order,axis=1)==np.sort(rt)).all(axis=1)
    err=np.abs(est-ref).sum(axis=1)/max(np.abs(ref).sum(),.02)
    mat=np.abs(ref)>=.02
    signs=np.sign(est).copy(); signs[np.abs(est)<=1e-12]=0
    return tops & (err<=.2) & (signs[:,mat]==np.sign(ref[mat])).all(axis=1)
auditrows=[]
for rec in r[(r.dataset=='german')&r.audit_error.notna()].itertuples(index=False):
    f=ROOT/'results/main'/f'{rec.dataset}_{rec.model}_{rec.seed}_{rec.slot:02d}.npz'
    with np.load(f,allow_pickle=False) as a:
        union=(a['reference']*2048+a['audit']*4096)/6144
        for im,method in enumerate(['kernel','perm']):
            for ip,p in enumerate([1,4,16]):
                est=a['attributions'][im,ip]
                mm=primary_labels(est,a['reference'])
                expected=i[(i.dataset=='german')&(i.model==rec.model)&(i.seed==rec.seed)&(i.slot==rec.slot)&(i.method==method)&(i.p==p)].success.iloc[0]
                assert np.isclose(mm.mean(),expected)
                aa=primary_labels(est,a['audit']); uu=primary_labels(est,union)
                auditrows.append(dict(model=rec.model,seed=rec.seed,slot=rec.slot,point=rec.point,
                    method=method,p=p,runs=64,merge_success=int(mm.sum()),
                    audit_success=int(aa.sum()),union_success=int(uu.sum()),
                    audit_label_discordant=int((mm!=aa).sum()),
                    union_label_discordant=int((mm!=uu).sum())))
ad=pd.DataFrame(auditrows)
ad.to_csv(OUT/'german_audit_label_sensitivity.csv',index=False)
# Counts rather than only small-stratum means; no cross-dataset aggregation.
gf=i[i.p==16].groupby(['dataset','model','method','gap_stratum']).agg(
    n=('point','size'),failed_runs=('success',lambda x:int(np.rint((1-x).sum()*64)))).reset_index()
gf.to_csv(OUT/'p16_failures_by_gap.csv',index=False)
assert (u[u.p==16].success==u[u.p==16].top3).all()
# Timing is 2 points x 5 seeds/cell, not 10 distinct patients.
nt=tr.groupby(['dataset','model','method','p']).size()
assert (nt==10).all() and len(tr)==540
assert (tr.rows==16*tr.requests).all()
t.to_csv(OUT/'uncached_timing.csv',index=False)
# Descriptive warning/extreme count check; do not replace any outlier.
l['huge']=l.error>1e6
libext=l.groupby(['dataset','mode','p']).agg(n=('error','size'),huge=('huge','sum'),
    maximum_error=('error','max')).reset_index()
libext.to_csv(OUT/'library_extremes.csv',index=False)
# Verify the protocol's pilot/main independence promise using stored outputs.
pilotrows=[]
for ds in ['acs','pima','german']:
    for model in ['lr','rf','hgb']:
        for slot in [0,1]:
            f=ROOT/'results/pilot'/f'{ds}_{model}_11_{slot:02d}.npz'
            main=ROOT/'results/main'/f.name
            hashes[str(f)]=sha(f)
            with np.load(f,allow_pickle=False) as ap, np.load(main,allow_pickle=False) as am:
                old=ap['attributions']; prefix=am['attributions'][:,:,:old.shape[2]]
                rec=dict(dataset=ds,model=model,slot=slot,
                    pilot_vectors=int(np.prod(old.shape[:-1])),
                    identical_main_prefix=bool(np.array_equal(old,prefix)),
                    max_absolute_difference=float(np.max(np.abs(old-prefix))),
                    pilot_qualified=bool(ap['qualified']),main_qualified=bool(am['qualified']),
                    reference_identical=bool(np.array_equal(ap['reference'],am['reference'])))
                if ds=='german':
                    rec.update(pilot_split_error=float(ap['split_error']),main_split_error=float(am['split_error']),
                        pilot_audit_qualified=bool(ap['audit_qualified']),main_audit_qualified=bool(am['audit_qualified']),
                        pilot_audit_error=float(ap['audit_error']),main_audit_error=float(am['audit_error']),
                        pilot_audit_pairs=len(ap['pairs_audit']),main_audit_pairs=len(am['pairs_audit']),
                        audit_prefix_identical=bool(np.array_equal(ap['pairs_audit'],am['pairs_audit'][:len(ap['pairs_audit'])])))
                pilotrows.append(rec)
pd.DataFrame(pilotrows).to_csv(OUT/'pilot_main_overlap.csv',index=False)
assert (u[u.p==16].error_pass==1).all() and (u[u.p==16].signok==1).all()
info=dict(command='python /work/analysis/findings_calculations.py',
    bootstrap='2000 percentile seed-stratified raw-ID cluster draws; RNG 20261111; 24 IDs per seed; paired contrasts reuse same IDs across methods/budgets; descriptive non-simultaneous intervals; no tests',
    definitions=dict(absolute_l1_mean='instance mean normalized L1 times max(reference L1,0.02)',
      absolute_regret_mean='instance mean normalized top3 regret times max(reference top3 absolute mass,0.02)',
      background_drift='L1(reference_B-reference_16)/max(L1(reference_16),0.02); each instance used once, not six times across methods/budgets'),
    counts=dict(cells=len(c),instance_method_budget_rows=len(i),point_fit_tasks=len(r),
                main_runs=len(u),background_rows=len(b),timing_records=len(tr),library_records=len(l)),
    floor_tasks=int((r.norm<.02).sum()),
    empty_material_tasks=int((i.drop_duplicates(['dataset','model','seed','slot']).material_n==0).sum()),
    maximum_main_efficiency_residual=float(raw.efficiency_max.max()),
    german_audit_pair_counts=raw[raw.audit_pairs>0][['dataset','model','seed','slot','audit_pairs']].to_dict('records'),
    input_sha256=hashes)
assert hashes=={p:sha(Path(p)) for p in hashes}, 'Input changed during analysis'
(OUT/'provenance.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps({k:v for k,v in info.items() if k not in ['input_sha256','definitions']},indent=2))
print('\nPAIRED CONTRASTS\n'+pd.DataFrame(contrasts).round(6).to_string(index=False))
print('\nBACKGROUND DRIFT\n'+bd.round(6).to_string(index=False))
print('\nGERMAN\n'+refsum.to_string())
print('\nGERMAN LABEL DISCORDANCE\n'+refdiscord.to_string(index=False))
print('\nFLOORS/EMPTY BY DATASET MODEL\n'+i.drop_duplicates(['dataset','model','seed','slot']).groupby(['dataset','model']).agg(floor=('floor','sum'),empty=('material_n',lambda x:int((x==0).sum()))).to_string())
