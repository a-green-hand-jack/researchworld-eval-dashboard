import sys,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from scipy.stats import t
root=Path('/hutian/paper-repo');sys.path.insert(0,str(root/'analysis'))
from benchmark import run_rep,METHODS
K=['k','ncal','scenario','shift','epsilon','alpha']
main=pd.concat([pd.read_json(root/'results'/f,lines=True) for f in ['main.jsonl','weighted.jsonl','prior_scores.jsonl']],ignore_index=True)
boundary=pd.read_json(root/'results/boundary.jsonl',lines=True)
assert len(main)==16000 and len(boundary)==4200
assert main.groupby(K+['method']).size().eq(100).all()
assert boundary.groupby(K+['method']).size().eq(50).all()
counts={'summary_values':0,'paired_values':0,'hashes':0,'inline_claims':0,'rerun_rows':0}
def select(df, row, keys):
 mask=np.ones(len(df),bool)
 for k in keys:mask &= np.isclose(df[k],row[k],atol=1e-14,rtol=0) if pd.api.types.is_float_dtype(df[k]) else (df[k]==row[k]).to_numpy()
 return df[mask]
def compare(v,row,col='mean'):
 a=np.array(v,dtype=float);a=a[np.isfinite(a)]
 assert len(a)==row['n_rep']
 if not len(a) or (col=='mean' and row.get('summary_status','')=='omitted_due_to_infinite_radius'):return
 mu=a.mean();assert abs(mu-row[col])<2e-12,(row,mu)
 if len(a)>1:
  half=t.ppf(.975,len(a)-1)*a.std(ddof=1)/np.sqrt(len(a))
  assert abs(mu-half-row.ci_low)<2e-12 and abs(mu+half-row.ci_high)<2e-12
for label,df in [('main',main),('boundary',boundary)]:
 summary=pd.read_csv(root/f'results/{label}_summary/summary.csv')
 for _,row in summary.iterrows():
  cell=select(df,row,K+['method']);compare(cell[row.metric],row);counts['summary_values']+=1
 pc=pd.read_csv(root/f'results/{label}_summary/paired_contrasts.csv')
 for _,row in pc.iterrows():
  c=select(df,row,K);pivot=c.pivot(index='seed',columns='method',values=row.metric)
  compare(pivot[row.method_a]-pivot[row.method_b],row,'mean_difference');counts['paired_values']+=1
for _,row in pd.read_csv(root/'results/main_summary/shift_contrasts.csv').iterrows():
 c=select(main,row,[k for k in K if k!='shift']+['method']);p=c.pivot(index='seed',columns='shift',values=row.metric)
 compare(p[True]-p[False],row,'mean_shift_minus_iid');counts['paired_values']+=1
manifest=json.loads((root/'presentation/artifact_manifest.json').read_text())
for section in ['generators','inputs','artifacts']:
 for path,h in (manifest[section].items() if isinstance(manifest[section],dict) else [(a['path'],a['sha256']) for a in manifest[section]]):
  assert hashlib.sha256((root/path).read_bytes()).hexdigest()==h,(section,path)
  counts['hashes']+=1
for claim in json.loads((root/'manuscript/claim_provenance.json').read_text()):
 p=root/claim['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==claim['sha256']
 c=select(pd.read_csv(p),claim['filters'],list(claim['filters']));assert len(c)==1
 vals=c.iloc[0][claim['columns']].astype(float).tolist()
 if len(vals)==3:assert f'{vals[0]:.4f} [{vals[1]:.4f}, {vals[2]:.4f}]'==claim['text']
 counts['inline_claims']+=1
for k in [3,10]:
 for ncal in [99,499]:
  for scenario in ['homogeneous','heterogeneous']:
   rows,_=run_rep(901000,k,ncal,scenario,ntest=5000,nvolume=8192,methods=METHODS+('clr_weighted','tv','kl_forward'))
   for row in rows:
    saved=select(main,row,K+['method','seed']).iloc[0]
    for metric in ['coverage','coverage_g0','coverage_g1','volume_fraction','mean_radius']:
     if row[metric] is not None:assert abs(saved[metric]-row[metric])<2e-12,(k,ncal,scenario,metric,saved[metric],row[metric])
    counts['rerun_rows']+=1
out={'head':'a71cdc607a6477ed8aa249ad218f456f141cc080','independent_audit':'passed','counts':counts}
Path('/tmp/internal-review24/independent_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
