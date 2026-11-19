"""Check real pilot exact games, in addition to analytic implementation tests."""
from pathlib import Path
import json,numpy as np
ROOT=Path(__file__).resolve().parents[1]
rows=[json.loads(l) for l in (ROOT/'results/pilot.jsonl').read_text().splitlines()]
exact=[json.loads(l) for l in (ROOT/'results/reference_pilot.jsonl').read_text().splitlines()]
checks=[]
for row in rows:
 if row['kind']=='estimator' and row['estimator']=='kernel' and row.get('exhaustive'):
  ref=next(x for x in rows if x['dataset']==row['dataset'] and x['model']==row['model'] and x.get('instance_index')==row['instance_index'] and x['kind']=='reference')
  diff=float(np.max(np.abs(np.array(row['phi'])-ref['phi'])))
  checks.append(dict(dataset=row['dataset'],model=row['model'],instance_index=row['instance_index'],check='exhaustive Kernel SHAP versus independent exact coalition sum',max_absolute_error=diff))
  if diff>1e-8:raise ValueError(f'exact game disagreement: {checks[-1]}')
for ref in exact:
 row=next(x for x in rows if x['dataset']=='german' and x['model']==ref['model'] and x.get('instance_index')==0 and x['kind']=='reference')
 checks.append(dict(dataset='german',model=ref['model'],instance_index=0,check='1024-path pilot reference versus exact reference (diagnostic, no acceptance cutoff)',max_absolute_error=float(np.max(np.abs(np.array(row['phi'])-ref['phi'])))))
(ROOT/'results/pilot_validation.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
