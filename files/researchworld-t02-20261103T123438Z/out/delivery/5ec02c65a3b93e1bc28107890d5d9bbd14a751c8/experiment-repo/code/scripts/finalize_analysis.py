"""Regenerate the complete derived evidence bundle and measure its actual cost.

--partial is an explicit timing/progress mode; it never certifies a final bundle.
"""
import argparse
import hashlib
import json
import resource
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
parser.add_argument('--partial',action='store_true')
parser.add_argument('--timing-output',type=Path,required=True,help='Keep under reproduction/, outside the results-only hash manifest')
args=parser.parse_args()
root=args.root.resolve()
scripts=Path(__file__).resolve().parent
completed=sum((root/'results/confirmatory'/r['name']/'summary.json').exists()
              for r in json.loads((root/'configs/confirmatory.json').read_text())['runs'])
start=time.perf_counter()
started=datetime.now(timezone.utc).isoformat()
steps=[]
base=[sys.executable]
commands=[
 ('audit',[str(scripts/'audit_registered.py'),'results/confirmatory','--output','results/registered-audit.json']+([] if args.partial else ['--require-complete'])),
 ('analyze',[str(scripts/'analyze.py'),'results/confirmatory','--registry','configs/confirmatory.json','--output','results/confirmatory-analysis']),
 ('predictions',[str(scripts/'study_analysis.py'),'results/confirmatory-analysis/runs.json','--output','results/confirmatory-analysis/predictions.json']),
 ('sensitivity',[str(scripts/'sensitivity.py'),'results/confirmatory','--registry','configs/confirmatory.json','--output','results/sensitivity']+([] if args.partial else ['--require-complete'])),
 ('inventory',[str(scripts/'inventory.py')])]
first=resource.getrusage(resource.RUSAGE_CHILDREN)
for label,command in commands:
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    clock=time.perf_counter()
    outcome=subprocess.run(base+command,cwd=root,check=False,capture_output=True,text=True)
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    steps.append(dict(stage=label,wall_s=time.perf_counter()-clock,
        child_cpu_s=(after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime),
        exit_code=outcome.returncode,stdout=outcome.stdout,stderr=outcome.stderr,
        source_sha256=hashlib.sha256(Path(command[0]).read_bytes()).hexdigest()))
    print(f'Derived stage {label}: exit{outcome.returncode}, wall{steps[-1]["wall_s"]:.3f}s',flush=True)
    if outcome.returncode:
        break
last=resource.getrusage(resource.RUSAGE_CHILDREN)
report=dict(kind='actual derived-tooling runtime; not training or fresh scientific replication',
    started_utc=started,ended_utc=datetime.now(timezone.utc).isoformat(),
    completed_input_runs=completed,registered_total=204,partial_mode=args.partial,
    all_stages_succeeded=len(steps)==len(commands) and all(s['exit_code']==0 for s in steps),
    end_to_end_wall_s=time.perf_counter()-start,
    child_cpu_s=(last.ru_utime+last.ru_stime)-(first.ru_utime+first.ru_stime),
    process_cpu_s=time.process_time(),child_peak_rss_kib=last.ru_maxrss,stages=steps,
    wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    scientific_completeness_note='Partial mode explicitly retains absent controls and is not final evidence. Default mode requires all204 in both raw audit and sensitivity.',
    clock_note='Child CPU includes process startup; peak child RSS is cumulative maximum, not summed simultaneous allocation. Owner semantic checking, Git transfer and independent review are separate work.')
args.timing_output.parent.mkdir(parents=True,exist_ok=True)
args.timing_output.write_text(json.dumps(report,indent=2)+'\n')
print('HUTIAN_WAKE: Derived pipeline finished '+json.dumps({k:report[k] for k in ['completed_input_runs','partial_mode','all_stages_succeeded','end_to_end_wall_s','child_cpu_s','child_peak_rss_kib']}),flush=True)
if not report['all_stages_succeeded']:
    raise SystemExit(1)
