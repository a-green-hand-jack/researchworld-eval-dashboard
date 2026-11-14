"""Deliberately selected measured near-tie failure; no new model evaluations."""
from pathlib import Path
import json,numpy as np
root=Path(__file__).resolve().parent
p=np.load(root/'results120/pima_mlp_11.npz');i=62
ref=p['reference'][i];a=p['phi'][i,:,3];names=['preg','plas','pres','skin','insu','mass','pedi','age']
target=set(np.argsort(-abs(ref),kind='stable')[:3]);matched=[set(np.argsort(-abs(x),kind='stable')[:3])==target for x in a]
counts={}
for x in a:
    key=','.join(names[j] for j in sorted(np.argsort(-abs(x),kind='stable')[:3]));counts[key]=counts.get(key,0)+1
ranks=np.argsort(-abs(ref),kind='stable')
report={'selection':'post hoc illustrative near-tie failure, not representative test','dataset':'pima','model':'mlp','seed':11,'audit_position':i,'source_row':int(p['instances'][i]),'budget':64,'matches':sum(matched),'repetitions':len(a),'rank3_4_gap':float(abs(ref[ranks[2]])-abs(ref[ranks[3]])),'reference':dict(zip(names,map(float,ref))),'estimated_sets_counts':counts,'first_repetition':dict(zip(names,map(float,a[0])))}
out=root/'paper_tables';out.mkdir(exist_ok=True)
(out/'failure_example.json').write_text(json.dumps(report,indent=2))
lines=[r'\begin{tabular}{lrr}',r'\toprule',r'Feature & Exact $\phi_j$ & First P64 estimate \\',r'\midrule']
for j in ranks: lines.append(f'{names[j]} & {ref[j]:.7f} & {a[0,j]:.7f} '+r'\\')
lines.extend([r'\bottomrule',r'\end{tabular}'])
(out/'failure_example.tex').write_text('\n'.join(lines)+'\n')
print(json.dumps(report,indent=2))
