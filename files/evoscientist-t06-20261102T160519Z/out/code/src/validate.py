"""Mechanical acceptance checks for data, witnesses, matching, uncertainty, and optional replay."""
import argparse,hashlib,json,re
from pathlib import Path
import numpy as np,pandas as pd
from prepare import load
from bt import BT
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'artifacts'

def main():
 p=argparse.ArgumentParser();p.add_argument('--replay',type=Path);args=p.parse_args();checks=[]
 manifest=json.loads((ROOT/'data/manifest.json').read_text())
 for item in manifest['files']:
  actual=hashlib.sha256((ROOT/item['file']).read_bytes()).hexdigest();assert actual==item['sha256'];checks.append('checksum:'+item['file'])
 ds,eda=load();base=pd.read_csv(A/'baseline.csv');witnesses=pd.read_csv(A/'witness_rows.csv')
 for r in base.itertuples():
  df,names=ds[r.dataset];sub=witnesses[witnesses.dataset==r.dataset];idx=sub.row_index.to_numpy(int)
  assert len(idx)==len(np.unique(idx))==r.k;assert np.all(df.iloc[idx].y!=.5)
  assert sub.row_id.astype(str).tolist()==df.iloc[idx].row_id.astype(str).tolist()
  new=df.y.to_numpy().copy();new[idx]=1-new[idx];m=BT(df.a,df.b,new,names);fit=m.fit()
  assert fit.grad<1e-7 and fit.theta[r.a]-fit.theta[r.b]<-1e-7
  assert abs(fit.theta[r.a]-fit.theta[r.b]-r.refit_gap)<1e-7
  assert abs(r.global_pct-100*r.k/r.n)<1e-10 and abs(r.exposure_pct-100*r.k/r.E)<1e-10
  assert r.incident_k==r.k and r.prior_gap>=-1e-7 and r.components==1
  checks.append('original-row witness:'+r.dataset)
 match=pd.read_csv(A/'matched.csv');ar=match[match.dataset=='arena_top6_n2400'];assert len(ar)==20 and ar.row_set_hash.nunique()==20 and (ar.n==2400).all()
 info=json.loads((A/'matching_protocol.json').read_text());assert info['arena_top6_pool_n']>info['arena_requested_n']==info['arena_actual_n']==2400;assert info['shared_cells']==1232
 checks.append('matching:20 distinct Arena subsets;1232 identical ordered MT support')
 human,_=ds['mt_human'];gpt,_=ds['mt_gpt4'];glookup=gpt.set_index('cell');eligible=human[human.cell.isin(glookup.index)]
 mismatches=0
 for row in eligible.itertuples():
  other=glookup.loc[row.cell]
  mismatches+=int(not (np.array_equal(row.conversation_a,other.conversation_a) and np.array_equal(row.conversation_b,other.conversation_b)))
 assert mismatches==0
 checks.append(f'matched MT answer representations: {mismatches} mismatches across {len(eligible)} eligible human rows; no text printed')
 controls=pd.read_csv(A/'controls.csv');assert len(controls)==6*4*100
 assert (controls.groupby(['dataset','method']).size()==100).all()
 boots=pd.read_csv(A/'uncertainty.csv');assert (boots.groupby('dataset').size()==200).all();assert 'witness_status' in boots
 checks.append('control/uncertainty repeat counts and statuses')
 compared=[]
 if args.replay:
  for f in ['eda.csv','baseline.csv','controls.csv','random_curves.csv','uncertainty.csv','adjacent.csv','rankings.csv','witness_rows.csv','ablations.csv','matched.csv','fixed_target_ablations.csv','method_comparison.csv','witness_verification.csv']:
   old=pd.read_csv(A/f);new=pd.read_csv(args.replay/'artifacts'/f)
   pd.testing.assert_frame_equal(old,new,check_exact=False,rtol=1e-8,atol=1e-9);compared.append(f)
  checks.append('isolated environment replay agrees on all 13 deterministic CSVs (runtime excluded)')
 # Only source scan; historical experiment logs legitimately preserve failures/TODOs.
 for fname in ['main.tex','appendix.tex','checklist_filled.tex']:
  text=(ROOT/'paper'/fname).read_text();assert not re.search(r'(?i)drafttodo|\bTODO\b|\bFIXME\b|\bXXX\b|placeholder',text),fname
 checks.append('manuscript has no unresolved markers')
 bib=(ROOT/'paper/references.bib').read_text();keys=set(re.findall(r'@\w+\s*\{\s*([^,]+),',bib));cited=set()
 for fname in ['main.tex','appendix.tex']:
  for group in re.findall(r'\\cite\w*\{([^}]+)\}',(ROOT/'paper'/fname).read_text()):cited.update(group.split(','))
 assert cited<=keys and len(keys)==5;checks.append('five actually-consulted literature entries; all cited keys resolve')
 report=dict(all_passed=True,checks=checks,replay_files=compared)
 (A/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
