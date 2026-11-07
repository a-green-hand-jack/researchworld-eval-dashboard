#!/usr/bin/env python3
"""Audit final result inventory and prescribed numerical evidence without refitting."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd

analysis=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(analysis/'src'))
from compbench.experiment import methods
from compbench.conformal import contains_case
spec=importlib.util.spec_from_file_location('allowance',analysis/'scripts/numerical_allowance.py')
allowance=importlib.util.module_from_spec(spec);spec.loader.exec_module(allowance)

p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--config',required=True);p.add_argument('--output',required=True);p.add_argument('--source-mode',choices=['git','files'],default='git');a=p.parse_args()
root=Path(a.root);config=Path(a.config);cfg=json.loads(config.read_text());execution=json.load(open(root/'execution.json'))
assert hashlib.sha256(config.read_bytes()).hexdigest()==execution['frozen_config_sha256']
manifest=[];metadata=[]
for s in [0,1]:
    m=json.load(open(root/f'shard_{s}/run_metadata.json'));metadata.append(m)
    assert m['config_sha256']==execution['frozen_config_sha256']
    assert 'finished_at_unix' in m
    assert m['volume_power']==cfg['volume_power'] and m['volume_centers']==cfg['volume_centers']
    for path,digest in m['source_hashes'].items():
        assert hashlib.sha256((analysis/path).read_bytes()).hexdigest()==digest,(path,'current source mismatch')
        if a.source_mode=='git':
            committed=subprocess.check_output(['git','show',execution['source_commit']+':analysis/'+path],cwd=analysis.parent)
            assert hashlib.sha256(committed).hexdigest()==digest,(path,'frozen source mismatch')
    audit_meta=json.load(open(root/f'shard_{s}/audit/metadata.json'))
    assert audit_meta['source_hashes']==m['source_hashes']
    assert audit_meta['config_sha256']==m['config_sha256']
    for f in sorted((root/f'shard_{s}/checkpoints').glob('*.json')):
        manifest.append({'path':str(f.relative_to(root)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
assert metadata[0]['source_hashes']==metadata[1]['source_hashes']
validation=json.load(open(root/'completeness_validation.json'));assert validation['status']=='passed'
assert validation['complete_trials']==len(manifest)==len(cfg['cells'])*cfg['repeats']
aud=pd.read_csv(root/'integration_audit.csv');policy=cfg['integration_validation']
expected=set();expected_main={}
for cell in cfg['cells']:
    if cell['k']!=3:continue
    for repeat in policy['outer_trial_repeats_for_audit']:
        paths=[root/f'shard_{s}/checkpoints/{cell["id"]}__{repeat}.json' for s in [0,1]]
        found=[p for p in paths if p.exists()];assert len(found)==1
        saved=json.load(open(found[0]));vv=pd.DataFrame(saved['volumes'])
        for name,_ in methods(cell['scenario'],cell.get('epsilon',.001),cell['alpha']):
            for group in ['majority','minority']:
                selected=vv[(vv.method==name)&(vv.group==group)].sort_values('test_index').iloc[:policy['centers_per_X_group_for_audit']]
                assert len(selected)==policy['centers_per_X_group_for_audit']
                for row in selected.itertuples():
                    key=(cell['id'],repeat,name,group,row.test_index);expected.add(key);expected_main[key]=row.volume
actual=list(aud[['cell','repeat','method','group','test_index']].itertuples(index=False,name=None))
assert len(set(actual))==len(actual) and set(actual)==expected
assert all(abs(row.main_volume-expected_main[(row.cell,row.repeat,row.method,row.group,row.test_index)])<1e-12 for row in aud.itertuples())
assert (aud.power==policy['high_resolution_power']).all()
assert (aud.n_scrambles==policy['independent_scrambles']).all()
assert np.isfinite(aud[['audit_volume','scramble_sd','main_volume']].to_numpy()).all()
for r in aud.itertuples():
    vals=np.array(json.loads(r.scramble_estimates));assert len(vals)==policy['independent_scrambles']
    assert np.isfinite(vals).all() and abs(vals.mean()-r.audit_volume)<1e-12
    assert abs(vals.std(ddof=1)-r.scramble_sd)<1e-12
recomputed,group_allowances=allowance.paired_audit(aud)
saved=pd.read_csv(root/'numerical_allowance/paired_integration_audit.csv')
keys=['cell','repeat','group','test_index','method','reference']
joined=saved.merge(recomputed,on=keys,suffixes=('_saved','_recomputed'),validate='one_to_one')
assert len(joined)==len(saved)==len(recomputed)
maxdiff=float((joined.empirical_allowance_saved-joined.empirical_allowance_recomputed).abs().max())
assert maxdiff<1e-12
contrasts=pd.read_csv(root/'numerical_allowance/area_contrasts_with_numerical_allowance.csv')
assert np.allclose(contrasts.enlarged_ci_low,contrasts.ci_low-contrasts.empirical_allowance,equal_nan=True)
assert np.allclose(contrasts.enlarged_ci_high,contrasts.ci_high+contrasts.empirical_allowance,equal_nan=True)
resolved=((contrasts.enlarged_ci_low>0)|(contrasts.enlarged_ci_high<0))&contrasts.empirical_allowance.notna()
assert (contrasts.numerically_resolved==resolved).all()
assert (contrasts.practically_rankable==(resolved&(contrasts['mean'].abs()>=cfg['interpretation_policy']['minimum_normalized_area_difference']))).all()
cases=[json.loads(line) for line in (root/'region_cases.jsonl').read_text().splitlines()]
assert len(cases)==32
for case in cases:
    assert bool(contains_case(case,np.array([case['original_y']]))[0])==case['covered']
    assert case['repeat']==case['test_index']==0 and case['cell'].endswith('_k3')
source_rows=pd.read_json(root/'trials.jsonl',lines=True)
assert not source_rows.duplicated(['id','repeat','method','group']).any()
assert source_rows[source_rows.status=='ok'].groupby(['id','method','group']).size().eq(cfg['repeats']).all()
# Every raw export and result table used in claims has a content digest.
files=[p for p in root.rglob('*') if p.is_file() and 'checkpoints' not in p.parts and p.name!='final_audit.json']
report={'source_verification_mode':a.source_mode,'postprocess_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'argv':sys.argv,'status':'passed','source_commit':execution['source_commit'],'expected_trials':len(manifest),
        'rows':len(source_rows),'numeric_rows':int((source_rows.status=='ok').sum()),
        'applicability_rows':int((source_rows.status!='ok').sum()),'audited_regions':len(aud),
        'matched_center_contrasts':len(saved),'paired_allowance_recalculation_max_difference':maxdiff,
        'max_empirical_allowance':float(group_allowances.empirical_allowance.max()),
        'numerically_unresolved_area_contrasts':int((~contrasts.numerically_resolved).sum()),
        'practically_rankable_area_contrasts':int(contrasts.practically_rankable.sum()),
        'area_contrasts':len(contrasts),'measured_region_cases':len(cases),
        'generation_failures':[str(p) for p in root.rglob('failure.json')],
        'numerical_range_warnings':validation['warnings'],
        'checkpoint_sha256':manifest,'file_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},
        'scope':'Completeness/source/numerical-policy audit, not independent report approval; empirical area allowances are not uniform bounds.'}
Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
print(f'Audit passed: {len(manifest)} trials; {len(aud)} audited regions; {len(saved)} matched-center contrasts; maximum allowance {report["max_empirical_allowance"]:.6f}',flush=True)
