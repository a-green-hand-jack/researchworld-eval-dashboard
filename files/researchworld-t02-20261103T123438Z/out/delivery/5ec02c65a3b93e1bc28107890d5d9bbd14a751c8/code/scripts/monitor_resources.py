"""Reconcile actual progress and reprice every remaining registered condition."""
import argparse
import json
import math
import hashlib
import sys
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from resource_forecast import affine_prefix_quote

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
parser.add_argument('--phase',choices=['first-completion-wake','checkpoint','before-follow-on','final'],required=True)
parser.add_argument('--output',required=True)
parser.add_argument('--resource-status',help='Optional freshly captured ht-resource status JSON')
parser.add_argument('--schedule',type=Path,help='Explicit prospective scenario/decision JSON; baseline history is always retained')
args=parser.parse_args()
root=args.root
registered=json.loads((root/'configs/confirmatory.json').read_text())['runs']
quote=json.loads((root/'results/gate-benchmarks/resource-quote.json').read_text())
prices={r['name']:r['projected_cpu_s'] for r in quote['run_quotes']}
ledger=json.loads((root/'reproduction/deadline_ledger.json').read_text())
now=datetime.now(timezone.utc)
deadline=datetime.fromisoformat(ledger['experimental_completion_deadline_utc'])
statuses=Counter()
runs=[]
rates=defaultdict(list)
wall_cpu_ratios=[]
for config in registered:
    directory=root/'results/confirmatory'/config['name']
    summary_path=directory/'summary.json'
    record=dict(name=config['name'],family=config['family'],width=config['width'],
                expected_steps=config['steps'],status='not_started',observed_step=0,cpu_s_lower_bound=0.)
    if (directory/'metadata.json').exists():
        record['status']='started_incomplete'
        rows=[]
        curve=directory/'curve.jsonl'
        if curve.exists():
            text=curve.read_text()
            lines=text.splitlines()
            for index,line in enumerate(lines):
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    if index!=len(lines)-1 or text.endswith('\n'):
                        raise
        if rows:
            row=rows[-1]
            record.update(observed_step=row['step'],cpu_s_lower_bound=row['cpu_s'],
                          wall_s_lower_bound=row['elapsed_s'])
        events_path=directory/'attempts.jsonl'
        events=[json.loads(line) for line in events_path.read_text().splitlines()] if events_path.exists() else []
        ends=[e for e in events if 'segment_cpu_s' in e]
        known=sum(e['segment_cpu_s'] for e in ends)
        record['cpu_s_lower_bound']=max(record['cpu_s_lower_bound'],known)
        if ends and ends[-1].get('status')=='failed':
            record['status']='failed_attempt_pending_recovery'
        if summary_path.exists():
            summary=json.loads(summary_path.read_text())
            record.update(status='completed',observed_step=summary['final']['step'],
                cpu_s_lower_bound=summary['cpu_s'],wall_s_lower_bound=summary['elapsed_s'])
        if record['observed_step']>=1000:
            rates[(config['family'],config['width'])].append(record['cpu_s_lower_bound']/record['observed_step'])
        if record['cpu_s_lower_bound']>0:
            wall_cpu_ratios.append(record.get('wall_s_lower_bound',0)/record['cpu_s_lower_bound'])
    statuses[record['status']]+=1
    runs.append(record)
remaining_s=0.
actual_s=sum(r['cpu_s_lower_bound'] for r in runs)
for record,config in zip(runs,registered):
    price=max(prices[record['name']],max(rates[(config['family'],config['width'])],default=0)*config['steps'])
    if record['status']=='completed':
        remaining=0.
    elif record['status']=='failed_attempt_pending_recovery':
        # Conservative quote assumes an entire new attempt, rather than assuming recovery saves work.
        remaining=price
    else:
        remaining=max(0,price-record['cpu_s_lower_bound'])
    record.update(repriced_full_cpu_s=price,remaining_cpu_s_projection=remaining)
    remaining_s+=remaining
# Actual preproduction loop/child CPU; keep startup accounting separate and explicit.
pilot_cpu=sum(json.loads(p.read_text())['cpu_s'] for folder in ['timing','pilot']
              for p in (root/'results'/folder).glob('*/summary.json'))
benchmark_cpu=sum(json.loads(p.read_text())['child_cpu_s']
                  for p in (root/'results/gate-benchmarks').glob('*end-to-end.json'))
validation_cpu=0.
for folder in ['implementation-checks','implementation-checks-v2']:
    for path in (root/'results'/folder).glob('*/attempts.jsonl'):
        validation_cpu+=sum(e.get('segment_cpu_s',0) for e in map(json.loads,path.read_text().splitlines()))
preproduction_cpu=pilot_cpu+benchmark_cpu+validation_cpu
startup_allowance=4*quote['startup_cpu_s_per_interpreter_upper_measured']
projected_total_h=(preproduction_cpu+actual_s+1.5*(remaining_s+startup_allowance))/3600
# Timed derived tools are a separate known component, never added as a resource
# aggregate that overlaps training. Other unmeasured tooling remains disclosed.
known_derived_tooling_cpu_s=0.
for timing_path in (root/'reproduction/derived-timing').glob('*.json'):
    timing=json.loads(timing_path.read_text())
    if timing.get('kind')=='actual derived-tooling runtime; not training or fresh scientific replication':
        known_derived_tooling_cpu_s+=timing['child_cpu_s']+timing['process_cpu_s']
known_software_tooling_cpu_s=0.
for timing_path in (root/'reproduction/checkpoints').glob('*software.json'):
    timing=json.loads(timing_path.read_text())
    if timing.get('kind')=='software fixture only; not a scientific observation or launch authorization':
        known_software_tooling_cpu_s+=timing['child_cpu_s']+timing['process_cpu_s']
with_known_tooling_h=projected_total_h+(known_derived_tooling_cpu_s+known_software_tooling_cpu_s)/3600
remaining_reserved_h=1.5*(remaining_s+startup_allowance)/3600
ratio=max(1.25,max(wall_cpu_ratios,default=1.))
serial_remaining_wall_h=remaining_reserved_h*ratio
hours_available=(deadline-now).total_seconds()/3600
files=[p for p in (root/'results').rglob('*') if p.is_file() and not p.name.endswith('.tmp')]
actual_archive_bytes=sum(p.stat().st_size for p in files)
prod_bytes=sum(p.stat().st_size for p in (root/'results/confirmatory').rglob('*')
               if p.is_file() and not p.name.endswith('.tmp'))
not_complete=len(registered)-statuses['completed']
per_run_bound=quote['conservative_all204_logical_archive_bytes']/204
remaining_storage=int(1.5*not_complete*per_run_bound)
own_workspace_bytes={}
for directory in [root,Path('/hutian/experiment-source-production'),Path('/hutian/experiment-source-gates')]:
    if directory.exists():
        own_workspace_bytes[str(directory)]=sum(p.stat().st_size for p in directory.rglob('*') if p.is_file())
resource=None
if args.resource_status:
    resource=json.loads(Path(args.resource_status).read_text())
report=dict(generated_utc=now.isoformat(),phase=args.phase,status_counts=dict(statuses),registered_total=len(registered),
    measured_preproduction_cpu_s=preproduction_cpu,production_observed_cpu_s_lower_bound=actual_s,
    remaining_cpu_hours_projection=remaining_s/3600,
    projected_complete_study_with_remaining50percent_reserve_cpu_hours=projected_total_h,
    additional_known_derived_tooling_cpu_s=known_derived_tooling_cpu_s,
    additional_known_software_tooling_cpu_s=known_software_tooling_cpu_s,
    projected_with_known_derived_tooling_and_remaining_reserve_cpu_hours=with_known_tooling_h,
    cap_cpu_hours=44,cap_headroom_hours=44-with_known_tooling_h,
    serial_remaining_wall_hours_with50percent_reserve_and_measured_ratio=serial_remaining_wall_h,
    measured_wall_per_cpu_factor_with_floor1p25=ratio,hours_until_experiment_target=hours_available,
    preserves_experiment_target_and_writing_review_reserves=serial_remaining_wall_h<hours_available,
    within_cpu_envelope=with_known_tooling_h<44,logical_results_bytes=actual_archive_bytes,
    actual_production_logical_bytes=prod_bytes,remaining_archive_with50percent_reserve_bytes=remaining_storage,
    projected_logical_results_plus_remaining_reserved_bytes=actual_archive_bytes+remaining_storage,
    own_workspace_logical_bytes=own_workspace_bytes,resource_snapshot=resource,runs=runs,
    caveats=['Running CPU is a latest-recorded lower bound, not completed-study compute.',
             'Rates are only revised upward from the registered per-run quote using measured same-family/width CPU.',
             'Remaining failed attempts are conservatively repriced as full reruns.',
             'Wall projection assumes serial execution with measured contention ratio floored at1.25; no twofold speedup.',
             'Preproduction includes measured pilot loops, benchmark child startup and validation loops; other unmeasured tooling is separate.'])
report['within_storage_envelope']=actual_archive_bytes+remaining_storage < quote['storage_limit_reference_bytes']
report['continue_unchanged_affordable_work']=report['within_cpu_envelope'] and report['preserves_experiment_target_and_writing_review_reserves'] and report['within_storage_envelope']
report['selected_gate']=dict(scenario='original registered schedule',authorized=True,
    continue_unchanged_affordable_work=report['continue_unchanged_affordable_work'])
if args.schedule:
    scenario=json.loads(args.schedule.read_text())
    assert scenario['registered_matrix_sha256']==hashlib.sha256((root/'configs/confirmatory.json').read_bytes()).hexdigest()
    handoff=datetime.fromisoformat(scenario['experimental_completion_deadline_utc'])
    target=datetime.fromisoformat(scenario['training_completion_deadline_utc'])
    derived_hours=float(scenario['final_derived_handoff_reserved_hours'])
    derived_cpu_hours=float(scenario['final_derived_cpu_allowance_hours'])
    assert math.isfinite(derived_hours) and derived_hours>0
    assert math.isfinite(derived_cpu_hours) and derived_cpu_hours>0
    assert (handoff-target).total_seconds() >= derived_hours*3600
    writing=datetime.fromisoformat(ledger['writing_figures_analysis_deadline_utc'])
    absolute=datetime.fromisoformat(ledger['absolute_one_week_deadline_utc'])
    assert deadline <= target < handoff < writing < absolute
    assert (absolute-writing).total_seconds() >= 48*3600
    floor=float(scenario['prospective_wall_per_cpu_factor'])
    assert math.isfinite(floor) and floor>=1.25
    excluded=set(scenario['excluded_historical_ratio_runs'])
    assert excluded<=set(r['name'] for r in registered)
    # New slowdowns/stalls always enter the prospective factor. Only the explicitly
    # recorded historical anomaly population can be excluded, never model outcomes.
    population=[r for r in runs if r['name'] not in excluded and r['cpu_s_lower_bound']>0]
    selected_ratio=max([floor]+[r.get('wall_s_lower_bound',0)/r['cpu_s_lower_bound'] for r in population])
    projected_wall=remaining_reserved_h*selected_ratio
    available=(target-now).total_seconds()/3600
    decision=scenario.get('decision') or {}
    source_revision=decision.get('source_revision','')
    authorized=(scenario['status']=='authorized' and decision.get('owner')=='story-repo'
        and len(source_revision)==40 and all(c in '0123456789abcdef' for c in source_revision)
        and bool(decision.get('path')))
    fits=projected_wall<available
    report['selected_gate']=dict(scenario=str(args.schedule),scenario_sha256=hashlib.sha256(args.schedule.read_bytes()).hexdigest(),
        authorized=authorized,decision=decision,target_utc=target.isoformat(),complete_package_handoff_utc=handoff.isoformat(),
        final_derived_handoff_reserved_hours=derived_hours,final_derived_cpu_allowance_hours=derived_cpu_hours,
        projected_complete_with_derived_cpu_allowance_hours=with_known_tooling_h+derived_cpu_hours,hours_available=available,
        selected_wall_per_cpu_factor=selected_ratio,baseline_prospective_factor=floor,
        excluded_historical_ratio_runs=sorted(excluded),observed_ratio_population=[r['name'] for r in population],
        remaining_reserved_serial_wall_hours=projected_wall,preserves_revised_target=fits,
        primary_data_and_original_false_gate_unchanged=True,
        continue_unchanged_affordable_work=bool(authorized and fits and with_known_tooling_h+derived_cpu_hours<44 and report['within_storage_envelope']))
    model=scenario.get('wall_forecast_model','max_latest_ratio_v1')
    if model not in ['max_latest_ratio_v1','elapsed_prefix_affine_v1']:
        raise ValueError('Unknown prospective wall forecast model')
    if model=='elapsed_prefix_affine_v1':
        affine=affine_prefix_quote(root,runs,excluded,floor,startup_allowance)
        report['unchanged_latest_ratio_selected_gate']=dict(report['selected_gate'])
        report['affine_prefix_forecast']=affine
        affine_cpu=(preproduction_cpu+actual_s+known_derived_tooling_cpu_s+known_software_tooling_cpu_s)/3600+affine['reserved_remaining_cpu_hours']+derived_cpu_hours
        fits=affine['reserved_wall_hours']<available
        report['selected_gate'].update(wall_forecast_model=model,
            selected_wall_per_cpu_factor=floor,
            selected_factor_semantics='Affine CPU slope only;all observed ratios/excesses remain separately retained',
            max_recorded_prefix_wall_per_cpu_ratio=affine['max_recorded_positive_cpu_wall_ratio'],
            max_recorded_elapsed_excess_s=affine['max_positive_elapsed_excess_s'],
            projected_complete_with_derived_cpu_allowance_hours=affine_cpu,
            remaining_reserved_serial_wall_hours=affine['reserved_wall_hours'],
            preserves_revised_target=fits,
            continue_unchanged_affordable_work=bool(authorized and fits and affine_cpu<44 and report['within_storage_envelope']))
    holds=[]
    for stop_path in (root/'results/resource-checkpoints').glob('guard-stop*-recovery.json'):
        stop=json.loads(stop_path.read_text())
        if stop.get('hold_new_training_until_superseding_story_decision'):
            failed_revision=stop['failed_story_decision_revision']
            superseded=set(scenario.get('supersedes_decision_revisions',[]))
            superseded.add(scenario.get('supersedes_decision_revision'))
            if source_revision==failed_revision or failed_revision not in superseded:
                holds.append(dict(path=str(stop_path),failed_story_decision_revision=failed_revision))
    report['selected_gate']['unresolved_explicit_guard_holds']=holds
    if holds:
        report['selected_gate']['continue_unchanged_affordable_work']=False
Path(args.output).parent.mkdir(parents=True,exist_ok=True)
Path(args.output).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['runs','resource_snapshot','caveats','own_workspace_logical_bytes']},indent=2))
