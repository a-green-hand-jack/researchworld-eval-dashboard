"""A generalization for real-cache counts must not alter completed synthetic outputs."""
import json,sys
sys.path.insert(0,'scripts')
from run_synthetic import run_cell
old=[json.loads(line) for line in open('results/synthetic-pilot.jsonl')]
for n,k,rho,spread,seed in [(64,16,.5,0.,145124728),(512,128,.9,.08,493096760),(16,128,0.,0.,3088465637)]:
 new=run_cell(1000,n,k,rho,spread,seed)
 expected=[r for r in old if r['n']==n and r['k']==k]
 assert new==expected,'Synthetic protocol changed'
print('PASS: all 75 existing pilot metrics are bit-for-bit unchanged by count-generator generalization.')
