"""Run an explicit grid; each config and every failed attempt remains recoverable."""
import argparse
import json
import sys
import subprocess
import traceback
import time
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from train import run

parser = argparse.ArgumentParser()
parser.add_argument('grid')
parser.add_argument('output')
parser.add_argument('--resume',action='store_true')
parser.add_argument('--wake-every',type=int,default=6)
parser.add_argument('--resource-root',type=Path,help='Optional live study root for a preconfiguration resource guard')
parser.add_argument('--resource-schedule',type=Path,help='Explicit authorized schedule/scenario; required with resource-root')
args = parser.parse_args()
if bool(args.resource_root) != bool(args.resource_schedule):
    parser.error('resource-root and resource-schedule must be supplied together')
grid = json.loads(Path(args.grid).read_text())
if isinstance(grid,dict):
    grid = grid['runs']
if len({item['name'] for item in grid}) != len(grid):
    raise ValueError('Duplicate run names')
if args.wake_every<1:
    raise ValueError('wake-every must be positive')
def latch_guard_stop(name, guard_output, reason):
    # Only an actually selected authorized schedule gets a durable shared hold.
    # A pending/test-only refusal does not manufacture an execution decision.
    scenario=json.loads(args.resource_schedule.read_text())
    decision=scenario.get('decision') or {}
    revision=decision.get('source_revision','')
    if scenario.get('status')!='authorized' or decision.get('owner')!='story-repo' or len(revision)!=40:
        return
    path=args.resource_root/'results/resource-checkpoints'/f'guard-stop-auto-{time.time_ns()}-recovery.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    record=dict(recorded_utc=datetime.now(timezone.utc).isoformat(),
        stop_reason=reason,trigger_guard_path=str(guard_output),before_configuration=name,
        hold_new_training_until_superseding_story_decision=True,
        failed_story_decision_revision=revision,
        recovery_note='Shared automatic hold after a preconfiguration guard failure;no later averaged fit clears it.A new actual supported story decision must explicitly supersede every unresolved failed revision.')
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(record,indent=2)+'\n')
    temporary.replace(path)

failed = []
completed = 0
for item in grid:
    name = item['name']
    config = {k:v for k,v in item.items() if k not in ('name','family','block','stage')}
    destination = Path(args.output)/name
    if (destination/'summary.json').exists():
        actual = json.loads((destination/'metadata.json').read_text())['config']
        if actual != config:
            raise ValueError(f'Completed-run configuration mismatch at {destination}')
        print(f'Skip completed run {name}',flush=True)
        continue
    if args.resource_root:
        guard_output=args.resource_root/'results/resource-checkpoints/guard'/Path(args.grid).stem/(name+'.json')
        command=[sys.executable,str(Path(__file__).resolve().parent/'monitor_resources.py'),
            '--root',str(args.resource_root),'--phase','checkpoint','--output',str(guard_output),
            '--schedule',str(args.resource_schedule)]
        checked=subprocess.run(command,check=False,capture_output=True,text=True)
        if checked.returncode:
            latch_guard_stop(name,guard_output,'Resource guard validation failed;hold all further launches')
            print(checked.stderr,flush=True)
            print(f'HUTIAN_WAKE: Resource guard could not validate before {name}; no new configuration launched',flush=True)
            raise SystemExit(3)
        guard=json.loads(guard_output.read_text())
        if not guard['selected_gate']['continue_unchanged_affordable_work']:
            latch_guard_stop(name,guard_output,'Selected resource guard failed;hold all further launches')
            print(f'HUTIAN_WAKE: Resource guard stopped before {name}; see {guard_output}; no new configuration launched',flush=True)
            raise SystemExit(3)
    try:
        run(config,destination,args.resume and (destination/'metadata.json').exists())
        completed += 1
        print(f'Completed run {name}',flush=True)
        if completed%args.wake_every==0:
            print(f'HUTIAN_WAKE: Completed {completed} configurations in {args.grid}; latest {name}',flush=True)
    except Exception:
        failed.append(name)
        traceback.print_exc()
        print(f'HUTIAN_WAKE: Failed run {name}',flush=True)
print(f'HUTIAN_WAKE: Grid ended with {completed} new completions and {len(failed)} failed configurations: {args.grid}',flush=True)
if failed:
    raise SystemExit(f'Failed configurations (retained): {failed}')
