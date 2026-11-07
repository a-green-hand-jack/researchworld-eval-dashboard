"""Reconstruct found primary attacks, check saved results, and expose edited rows."""
import json
import numpy as np,pandas as pd
from datasets import primary,ROOT
from bt import fit,influence
out=ROOT/'results/witnesses';out.mkdir(parents=True,exist_ok=True);rows=[]
for d in primary():
 saved=json.loads((ROOT/'results/primary'/d.name/'audit.json').read_text());a,b,y,names=d.arrays();t,diag=fit(a,b,y,len(names));indices,gain,pair=influence(a,b,y,t)
 assert abs(t[pair[0]]-t[pair[1]]-saved['gap'])<1e-10
 k=saved['attack_k'];ix=indices[:k];z=y.copy();z[ix]=1-z[ix];u,diag2=fit(a,b,z,len(names),init=t)
 assert len(ix)==k and u[pair[0]]<u[pair[1]]
 assert abs(u[pair[0]]-u[pair[1]]-saved['attack_margin_at_k'])<1e-10
 w=d.frame.iloc[ix].copy();w.insert(0,'processed_row_index',ix);w['new_y']=1-w.y;w['influence_margin_reduction']=gain[ix];w.to_csv(out/(d.name+'.csv'),index=False)
 rows.append(dict(dataset=d.name,k=k,distinct_indices=len(set(ix)),old_margin=float(t[pair[0]]-t[pair[1]]),new_margin=float(u[pair[0]]-u[pair[1]]),gradient=diag2['gradient_max']))
pd.DataFrame(rows).to_csv(out/'verification.csv',index=False)
print('PASS: every primary found attack reconstructed and all changed rows saved')
