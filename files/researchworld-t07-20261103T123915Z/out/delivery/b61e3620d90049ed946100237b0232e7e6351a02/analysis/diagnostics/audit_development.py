"""Audit completed source-only fits and development choices without target scores."""
import hashlib,json,pathlib
import numpy as np
import pandas as pd
from benchsmall.pipeline import Study,choose,check_freeze,digest,read,write
root=pathlib.Path(__file__).resolve().parents[1]
check_freeze(root);study=Study(root);fits=[];cases=[];manifest={};parameters=[]
for b,bb in study.splits.items():
 x,unused=study.data(b,'main')
 for scenario,split in bb['scenarios'].items():
  directory=study.out/'fits'/b/scenario
  for path in sorted(directory.glob('*.json')):
   r=read(path);stage=r['stage'];rows=split['train' if stage=='development' else 'history'];source=x[rows]
   assert r['source_hash']==digest(source) and r['source_rows']==len(rows)
   fit=np.load(path.with_suffix('.npz'));assert fit['a'].shape==(x.shape[1],r['dimension'])
   assert fit['b'].shape==(x.shape[1],) and fit['theta'].shape==(len(rows),r['dimension'])
   assert all(np.isfinite(fit[k]).all() for k in fit.files)
   for file in [path,path.with_suffix('.npz')]:manifest[str(file.relative_to(root))]=hashlib.sha256(file.read_bytes()).hexdigest()
   suspended=b=='mmlu_pro' and scenario=='main' and stage=='development' and r['dimension']==15
   fits.append({'benchmark':b,'scenario':scenario,'stage':stage,'dimension':r['dimension'],
    'source_rows':len(rows),'source_hash':r['source_hash'],'converged':r['fit_info']['converged'],
    'attempts':len(r['fit_info']['attempts']),'total_iterations':sum(a['iterations'] for a in r['fit_info']['attempts']),
    'objective':r['fit_info']['objective'],'gradient_max':r['fit_info']['gradient_max'],
    'elapsed_seconds_raw':r['seconds'],'known_suspension_affected':suspended,'peak_process_rss_kib':r['peak_process_rss_kib']})
  output=study.out/'development'/b/f'{scenario}.json'
  if not output.exists():
   cases.append({'benchmark':b,'scenario':scenario,'complete':False});continue
  r=read(output);assert r['n_train']==len(split['train']) and r['n_validation']==len(split['validation']) and r['n_history']==len(split['history']) and r['n_target_reserved']==len(split['target'])
  for budget,selected in r['selection'].items():
   for name,value in selected['parameters'].items():
    parameters.append({'benchmark':b,'scenario':scenario,'budget':int(budget),'parameter':name,'selected_value':value,'n_fit':r['n_train'],'n_validation':r['n_validation'],'n_history':r['n_history'],'n_reserved_target':r['n_target_reserved']})
   for method,losses in selected['development_losses'].items():
    assert np.isfinite([v for k,v in losses]).all()
    name='mirt_random_mix' if method=='mirt_random_mix' else 'mirt_anchor_mix' if method=='mirt_anchor_mix' else method
    assert selected['parameters'][name]==choose(losses),(b,scenario,budget,method)
   refit=read(directory/f"refit_d{selected['parameters']['mirt_dimension']}.json")
   assert refit['fit_info']['converged']
  manifest[str(output.relative_to(root))]=hashlib.sha256(output.read_bytes()).hexdigest()
  cases.append({'benchmark':b,'scenario':scenario,'complete':True,'n_fit':r['n_train'],'n_development':r['n_validation'],'n_history':r['n_history'],'n_reserved_target':r['n_target_reserved'],'selected_refit_dimensions':json.dumps(r['refit_dimensions'])})
pd.DataFrame(fits).to_csv(study.out/'fit_diagnostics.csv',index=False)
pd.DataFrame(cases).to_csv(study.out/'development_completeness.csv',index=False)
write(study.out/'source_artifact_manifest.json',manifest)
pd.DataFrame(parameters).sort_values(['benchmark','scenario','budget','parameter']).to_csv(study.out/'development_parameters.csv',index=False)
print('Audited',len(fits),'source fits;',sum(r['complete'] for r in cases),'of',len(cases),'scenario development/refit packages complete; no target scores used.')
