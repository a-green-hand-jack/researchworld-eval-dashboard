"""Isolated guard software checks; no scientific run or genuine approval created."""
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime,timedelta,timezone
from pathlib import Path

repo=Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary)
    for rel in ['configs/confirmatory.json','results/gate-benchmarks/resource-quote.json','reproduction/deadline_ledger.json']:
        path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((repo/rel).read_bytes())
    now=datetime.now(timezone.utc)
    ledger=json.loads((root/'reproduction/deadline_ledger.json').read_text())
    ledger.update(experimental_completion_deadline_utc=(now-timedelta(hours=1)).isoformat(),
        writing_figures_analysis_deadline_utc=(now+timedelta(days=5)).isoformat(),
        absolute_one_week_deadline_utc=(now+timedelta(days=7)).isoformat())
    (root/'reproduction/deadline_ledger.json').write_text(json.dumps(ledger))
    scenario=dict(status='proposed_pending_story_authorization',
        registered_matrix_sha256=hashlib.sha256((root/'configs/confirmatory.json').read_bytes()).hexdigest(),
        experimental_completion_deadline_utc=(now+timedelta(days=3)).isoformat(),
        training_completion_deadline_utc=(now+timedelta(days=3,hours=-.5)).isoformat(),
        final_derived_handoff_reserved_hours=.5,final_derived_cpu_allowance_hours=.1,
        prospective_wall_per_cpu_factor=1.860141102946608,
        excluded_historical_ratio_runs=['frozen_w512_b06','frozen_w512_b07'],decision=None)
    schedule=root/'SOFTWARE_FIXTURE_SCENARIO.json';schedule.write_text(json.dumps(scenario))
    output=root/'report.json'
    command=[sys.executable,str(repo/'code/scripts/monitor_resources.py'),'--root',str(root),
        '--phase','checkpoint','--output',str(output),'--schedule',str(schedule)]
    def check():
        subprocess.run(command,check=True,stdout=subprocess.DEVNULL)
        return json.loads(output.read_text())
    report=check()
    assert not report['continue_unchanged_affordable_work'] # expired original schedule
    assert report['selected_gate']['preserves_revised_target']
    assert not report['selected_gate']['authorized']
    assert not report['selected_gate']['continue_unchanged_affordable_work']
    grid=root/'one-software-fixture-grid.json'
    registry=json.loads((root/'configs/confirmatory.json').read_text())['runs']
    grid.write_text(json.dumps([registry[0]]))
    destination=root/'guard-blocked-output'
    stopped=subprocess.run([sys.executable,str(repo/'code/scripts/run_grid.py'),str(grid),str(destination),
        '--resource-root',str(root),'--resource-schedule',str(schedule)],capture_output=True,text=True)
    assert stopped.returncode==3,stopped.stderr
    assert 'no new configuration launched' in stopped.stdout
    assert not destination.exists() # no trainer invocation
    # Structural approved-decision fixture only. Not a real authorization/source.
    scenario.update(status='authorized',decision=dict(owner='story-repo',source_revision='0'*40,path='SOFTWARE_FIXTURE'))
    schedule.write_text(json.dumps(scenario))
    report=check()
    assert report['selected_gate']['continue_unchanged_affordable_work']
    costs=root/'reproduction/derived-timing';costs.mkdir(parents=True)
    (costs/'software-fixture.json').write_text(json.dumps(dict(
        kind='actual derived-tooling runtime; not training or fresh scientific replication',child_cpu_s=12.,process_cpu_s=3.)))
    report=check()
    assert report['additional_known_derived_tooling_cpu_s']==15.
    assert abs(report['selected_gate']['projected_complete_with_derived_cpu_allowance_hours']-
        (report['projected_complete_study_with_remaining50percent_reserve_cpu_hours']+15/3600+.1))<1e-10
    software=root/'reproduction/checkpoints';software.mkdir(parents=True)
    (software/'fixture-software.json').write_text(json.dumps(dict(
        kind='software fixture only; not a scientific observation or launch authorization',process_cpu_s=4.,child_cpu_s=.5)))
    report=check()
    assert report['additional_known_software_tooling_cpu_s']==4.5
    assert abs(report['selected_gate']['projected_complete_with_derived_cpu_allowance_hours']-
        (report['projected_complete_study_with_remaining50percent_reserve_cpu_hours']+19.5/3600+.1))<1e-10
    directory=root/'results/confirmatory/frozen_w512_b06' ;directory.mkdir(parents=True)
    (directory/'metadata.json').write_text('{}')
    (directory/'curve.jsonl').write_text(json.dumps(dict(step=1000,cpu_s=1.,elapsed_s=1000000.))+'\n')
    report=check()
    assert report['measured_wall_per_cpu_factor_with_floor1p25']==1000000.
    assert report['selected_gate']['selected_wall_per_cpu_factor']==scenario['prospective_wall_per_cpu_factor']
    directory=root/'results/confirmatory/main_w032_b00';directory.mkdir(parents=True)
    (directory/'metadata.json').write_text('{}')
    (directory/'curve.jsonl').write_text(json.dumps(dict(step=1000,cpu_s=1.,elapsed_s=1000000.))+'\n')
    report=check()
    assert report['within_cpu_envelope']
    assert report['selected_gate']['selected_wall_per_cpu_factor']==1000000.
    assert not report['selected_gate']['continue_unchanged_affordable_work'] # new stall cannot be ignored
    # A genuinely selected structural fixture now fails the live resource gate.
    # No trainer invocation; failure atomically latches a shared hold before exit.
    stopped=subprocess.run([sys.executable,str(repo/'code/scripts/run_grid.py'),str(grid),str(destination),
        '--resource-root',str(root),'--resource-schedule',str(schedule)],capture_output=True,text=True)
    assert stopped.returncode==3 and not destination.exists(),stopped.stderr
    holds=list((root/'results/resource-checkpoints').glob('guard-stop-auto-*-recovery.json'))
    assert len(holds)==1
    hold=json.loads(holds[0].read_text())
    assert hold['failed_story_decision_revision']=='0'*40
    (directory/'curve.jsonl').write_text(json.dumps(dict(step=1000,cpu_s=1.,elapsed_s=1.))+'\n')
    report=check()
    assert report['selected_gate']['preserves_revised_target']
    assert not report['selected_gate']['continue_unchanged_affordable_work']
    scenario['decision']['source_revision']='1'*40
    scenario['supersedes_decision_revision']='0'*40
    schedule.write_text(json.dumps(scenario))
    assert check()['selected_gate']['continue_unchanged_affordable_work']
    second=holds[0].with_name('guard-stop-second-recovery.json')
    later=dict(hold,failed_story_decision_revision='1'*40)
    second.write_text(json.dumps(later))
    scenario['decision']['source_revision']='2'*40
    scenario['supersedes_decision_revision']='1'*40
    schedule.write_text(json.dumps(scenario))
    assert not check()['selected_gate']['continue_unchanged_affordable_work']
    scenario['supersedes_decision_revisions']=['0'*40,'1'*40]
    schedule.write_text(json.dumps(scenario))
    assert check()['selected_gate']['continue_unchanged_affordable_work']
print('PASS: automatic shared hold survives later fit;all failed decisions require explicit supersession;known software CPU retained. Software fixtures only.')
print('PASS: pending decision blocks trainer; original failed gate retained; structural schedule selection; only named historical gaps excluded; new stalls stop work. Software fixtures only.')
