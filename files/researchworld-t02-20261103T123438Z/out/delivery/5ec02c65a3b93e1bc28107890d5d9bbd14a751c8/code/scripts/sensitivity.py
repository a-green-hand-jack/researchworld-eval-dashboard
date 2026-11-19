"""Registered threshold/persistence sensitivities from complete measured curves."""
import argparse
import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('root')
parser.add_argument('--registry',default='configs/confirmatory.json')
parser.add_argument('--output',required=True)
parser.add_argument('--require-complete',action='store_true')
args = parser.parse_args()
out = Path(args.output)
out.mkdir(parents=True,exist_ok=True)
scripts = Path(__file__).resolve().parent
variants = [dict(train_threshold=t,valid_threshold=v,sustain=s,thin=1)
            for t,v,s in itertools.product([.95,.99],[.90,.95,.99],[1,3])]
variants.append(dict(train_threshold=.99,valid_threshold=.95,sustain=3,thin=2))
summary = []
for variant in variants:
    name = 't%d-v%d-s%d-thin%d'%(round(100*variant['train_threshold']),
        round(100*variant['valid_threshold']),variant['sustain'],variant['thin'])
    destination = out/name
    command = [sys.executable,str(scripts/'analyze.py'),args.root,'--registry',args.registry,'--output',str(destination)]
    for key,value in variant.items():
        command.extend(['--'+key.replace('_','-'),str(value)])
    subprocess.run(command,check=True,stdout=subprocess.DEVNULL)
    provenance = json.loads((destination/'analysis.json').read_text())
    complete = provenance['completed']==provenance['registered_total'] and not provenance['incomplete'] and not provenance['absent_registered_runs']
    if args.require_complete and not complete:
        raise SystemExit('Sensitivity requires the entire registered matrix; no partial inference')
    subprocess.run([sys.executable,str(scripts/'study_analysis.py'),str(destination/'runs.json'),
                    '--output',str(destination/'predictions.json')],check=True,stdout=subprocess.DEVNULL)
    predictions = json.loads((destination/'predictions.json').read_text())
    summary.append(dict(name=name,**variant,complete=complete,path=str(destination),
        P1=predictions['P1'],P2=predictions['P2'],P3=predictions['P3'],
        run_statistics_sha256=hashlib.sha256((destination/'runs.json').read_bytes()).hexdigest(),
        boundary_note=provenance['thinning_boundary_note']))
report = dict(variants=summary,number_variants=len(variants),
    primary=dict(train_threshold=.99,valid_threshold=.95,sustain=3,thin=1),
    scope='Secondary, pointwise threshold/persistence recomputation from the same measured curves. Primary decisions remain fixed.',
    cadence_caveat='The thin2 variant uses only measured200-step observations, with60200 execution end. Onset at60000 cannot have three-point confirmation here; no60400 observation is invented.',
    matrix_sha256=hashlib.sha256(Path(args.registry).read_bytes()).hexdigest())
(out/'sensitivity.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(f'Wrote{len(variants)} sensitivity variants; completeness retained per variant')
