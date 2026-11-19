"""Small, audited metadata export for analysis without shipping the 723 MB payoff cache."""
from common import *
import json,hashlib
rows=[]
for ds in DATASETS:
 for md in MODELS:
  for case in range(N_CASES):
   p=ROOT/f'results/games/{ds}_{md}_{case:02d}_b16.npz';a=np.load(p);v=a['v'];phi=a['phi']
   rows.append(dict(dataset=ds,model=md,case=case,file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),phi=phi.tolist(),v_empty=float(v[0]),v_full=float(v[-1]),seconds=float(a['seconds']),cpu_seconds=float(a['cpu_seconds']),efficiency_error=float(abs(phi.sum()-(v[-1]-v[0])))))
(ROOT/'results/reference_summary.json').write_text(json.dumps(rows,indent=2));print('exported',len(rows),'actual reference tables')
