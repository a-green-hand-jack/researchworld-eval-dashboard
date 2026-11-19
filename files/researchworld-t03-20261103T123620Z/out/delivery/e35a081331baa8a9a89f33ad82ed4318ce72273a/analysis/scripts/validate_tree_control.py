"""Independent exact Tree SHAP check for probability-averaging random forests.

This control is limited to random forest probabilities. Do not substitute a
nonlinear boosted-output transform without a common-game identity proof/check.
"""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import joblib,numpy as np,shap
pilot=[json.loads(l) for l in (ROOT/'results/pilot.jsonl').read_text().splitlines()]
german=[json.loads(l) for l in (ROOT/'results/reference_pilot.jsonl').read_text().splitlines()]
rows=[]
for dataset in ['german','acs','diabetes']:
 b=joblib.load(ROOT/f'artifacts/pilot/{dataset}_forest.joblib')
 explainer=shap.TreeExplainer(b['model'],data=b['background'],feature_perturbation='interventional',model_output='probability')
 for i in range(1 if dataset=='german' else 2):
  ref=next(r['phi'] for r in (german if dataset=='german' else pilot) if r['dataset']==dataset and r['model']=='forest' and r.get('instance_index')==i and (dataset=='german' or r['kind']=='reference'))
  start=time.perf_counter();phi=np.asarray(explainer.shap_values(b['instances'][i][None,:],check_additivity=True))[0,:,1]
  diff=float(np.max(abs(phi-ref)))
  pred=float(b['model'].predict_proba(b['instances'][i][None,:])[0,1]); baseline=float(b['model'].predict_proba(b['background'])[:,1].mean())
  rows.append(dict(dataset=dataset,model='forest',instance_index=i,max_absolute_error=diff,reference_phi=ref,tree_phi=phi.tolist(),tree_wall_seconds=time.perf_counter()-start,tree_expected_value=float(explainer.expected_value[1]),model_background_mean=baseline,tree_efficiency_residual=float(phi.sum()-(pred-baseline)),reference_efficiency_residual=float(np.sum(ref)-(pred-baseline)),reference='direct exact empirical-game enumeration',control='TreeExplainer interventional positive-class probability',passed_1e_minus6_check=diff<=1e-6))
  # Tree SHAP's C++ arithmetic has lower precision; document the measured error.
  print(dataset,i,'Tree SHAP max difference',diff,flush=True)
(ROOT/'results/tree_control_validation.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
