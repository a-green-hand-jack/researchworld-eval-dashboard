"""Contract/target checks on artificial binary fixture; no LLM result is implied."""
import json,pathlib,subprocess,sys,tempfile
import numpy as np
import pandas as pd
sys.path.insert(0,'scripts')
from finite_population import hypergeom_interval
ids=[0,1,2,9,10,13,14,15]
with tempfile.TemporaryDirectory() as folder:
 p=pathlib.Path(folder)
 scores=np.random.default_rng(478).integers(0,2,size=(80,8),dtype=np.uint8)
 scores[:32,0]=np.tile([0,1],16);scores[32:,0]=np.tile([0,1],24)
 scores[:32,3]=1;scores[32:,3]=0
 # Unique full-search winner 9; baseline audit .5; primary contrast -.5.
 for c in [1,2,4,5,6,7]:scores[0,c]=0
 np.savez_compressed(p/'fixture.npz',scores=scores,candidate_ids=ids,pools=np.array(['search']*32+['audit']*48),categories=np.array(['fixture_category']*80))
 (p/'partition.json').write_text(json.dumps(dict(n_search=32,n_audit=48,candidate_order=[0,14,9,13,1,10,15,2])))
 subprocess.run([sys.executable,'scripts/analyze_disjoint.py','--matrix',str(p/'fixture.npz'),'--partition',str(p/'partition.json'),'--reps','50','--out-dir',str(p/'out')],check=True,stdout=subprocess.DEVNULL)
 primary=json.loads((p/'out/primary-result.json').read_text())
 assert primary['candidate_id']==9 and primary['reused_score']==1.
 assert primary['audit_accuracy']==0. and primary['reused_minus_audit']==1.
 assert primary['logical_selected_accuracy_audit_calls']==48
 assert primary['logical_selected_default_paired_audit_calls']==96
 assert primary['logical_search_plus_paired_audit_calls']==32*8+96
 assert primary['paired_audit_contrast_to_default']==-.5
 assert not primary['paired_audit_positive_claim']
 total=hypergeom_interval(32,32,12032,.05/8)
 assert np.allclose(primary['exact_simultaneous_remaining_interval'],np.clip((12032*np.array(total)-32)/12000,0,1))
 assert np.allclose(primary['exact_audit_interval'],hypergeom_interval(0,48,12000))
 candidates=pd.read_csv(p/'out/candidate-audit.csv').set_index('candidate_id')
 assert candidates.loc[9,'paired_wins']==0 and candidates.loc[9,'paired_losses']==24
 assert (candidates.audit_population_questions==12000).all()
 frequencies=pd.read_csv(p/'out/selection-frequencies.csv')
 assert np.allclose(frequencies.groupby(['n','k']).full_selection_frequency.sum(),1.)
 conditional=pd.read_csv(p/'out/conditional-selection.csv')
 assert np.isfinite(conditional[['mean','mcse']]).all().all()
 gaps=conditional[conditional.metric.isin(['reused_minus_audit','split_report_minus_audit'])]
 assert (gaps.audit_simultaneous_gap_lower<=gaps.audit_simultaneous_gap_upper).all()
 assert set(pd.read_csv(p/'out/candidate-correlation.csv',index_col=0).index)==set(ids)
 subprocess.run([sys.executable,'scripts/analyze_disjoint.py','--matrix',str(p/'fixture.npz'),'--partition',str(p/'partition.json'),'--reps','50','--out-dir',str(p/'adjusted'),'--design-count','2','--actual-generated-responses','1280'],check=True,stdout=subprocess.DEVNULL)
 adjusted=json.loads((p/'adjusted/primary-result.json').read_text())
 assert adjusted['candidate_id']==primary['candidate_id']
 assert adjusted['design_count']==2 and adjusted['per_design_alpha']==.025
 assert adjusted['actual_cache_calls']==1280 and adjusted['analysis_cache_responses']==640
 assert np.allclose(adjusted['exact_audit_interval'],hypergeom_interval(0,48,12000,.025))
 total_adjusted=hypergeom_interval(32,32,12032,.025/8)
 assert np.allclose(adjusted['exact_simultaneous_remaining_interval'],np.clip((12032*np.array(total_adjusted)-32)/12000,0,1))
 assert adjusted['exact_audit_interval'][1]>=primary['exact_audit_interval'][1]
print('PASS: artificial-fixture primary identity, complement target, paired contrast, conditional mixtures and export contract')
