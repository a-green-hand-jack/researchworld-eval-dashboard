"""Whole-study known/unknown computation accounting, without inferred CPU costs.

Disjoint process-clock intervals form a documented subtotal. Sampled resource
accounting, wall-only measurements and absent timers stay separate currencies.
"""
import argparse,csv,hashlib,json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--input',default='results');a=p.parse_args();r=ROOT/a.input
rows=[]
def row(stage,cpu,source,scope,**kw):
    rows.append(dict(stage=stage,cpu_seconds=cpu,source=source,scope=scope,add_to_disjoint_process_clock_subtotal=cpu is not None,**kw))
def load(name):return json.loads((r/name).read_text())
main=pd.read_csv(r/'job_costs.csv');maincpu=float(main.process_total_cpu_seconds.sum())
row('primary_main_all_nine_cells',maincpu,'job_costs.csv','whole-process CPU for nine completed jobs; includes fitting/preprocessing/imports/references/calls/writing')
for name,title in [('pilot.jsonl','initial_pilot'),('budget_pilot.jsonl','dimension_specific_budget_pilot'),('reference_pilot.jsonl','first_German_exact_reference_pilot'),('final_precision_pilot.jsonl','float64_retiming_pilot')]:
    records=[json.loads(s) for s in (r/name).read_text().splitlines()]
    cpu=sum(z.get('cpu_seconds',z.get('info',{}).get('train_cpu_seconds',0)) for z in records)
    row(title,float(cpu),name,'sum recorded nonoverlapping model-fit/call/reference intervals; excludes startup, raw loading, untimed prediction/setup and writing',n_records=len(records))
pre=load('acs_preflight.json')
row('fresh_ACS_full_pipeline_preflight',pre['total_cpu_seconds'],'acs_preflight.json','single outer process-clock interval after imports; contains prepare/exact/exhaustive-Kernel/six stochastic checks; inner checks NOT added again')
for name in ['smoke_initial','smoke_intermediate','smoke_final','fresh_reproduction_preflight']:
    source='computation_ledger/source_records/'+name+'.json';z=load(source)
    row(name,z['process_total_cpu_seconds'],source,'whole-process timer for this distinct actual development/reproduction run; not main-panel replication',n_completed_inputs=z['n_completed'])
row('changed_background_cost_pilot',float(pd.read_csv(r/'background_pilot/summary/job_costs.csv').process_cpu_seconds.sum()),'background_pilot/summary/job_costs.csv','six outer cell-phase timers, after imports/bundle/data loading; internal exact/call timers NOT added again')
row('full_changed_background_arm',float(pd.read_csv(r/'background_sensitivity/job_costs.csv').process_cpu_seconds.sum()),'background_sensitivity/job_costs.csv','six outer cell-phase timers, after imports/bundle/data loading; internal exact/call timers NOT added again')
unknown=[
 ('failed_exploratory_TreeExplainer_control','tree_control_validation.json','five unsuccessful retained comparisons have tree_wall_seconds only; no CPU clock. First strict abort is a separate uninstrumented attempt.'),
 ('pre_float64_common_game_failures','notes/development-log.md','initial strict check and attempted output-only precision correction failed before input casting; no retained CPU timer'),
 ('final_common_game_validation','common_game_validation.json','12 successful exhaustive-Kernel/direct checks; no retained CPU timer'),
 ('ACS_loading_optimization_checks','loading_check.json','final loader has elapsed4.17698s only; earlier streaming/chunking checks also not retained with process clocks'),
 ('setup_parser_and_dtype_corrections','notes/development-log.md','early Pandas category/dtype errors; no trained numerical result before fixes, no CPU clock retained'),
 ('data_acquisition_environment_and_library_warmup','data/manifest.json; environment-versions.json; notes/development-log.md','network acquisition/install/font-cache warmup and setup lack CPU clocks; not treated as zero'),
 ('untracked_tests_and_statistical_validation','tests; boundary_guard_validation.json; notes/development-log.md','analytic/metric tests, boundary checks, seed/identity/preflight diagnostics and repeated local runs are uninstrumented'),
 ('untracked_audit_aggregation_and_delivery_checks','scripts; panel_audit.json; delivery_panel_audit.json','repeated local progress audits, smoke aggregation, integrated checks and ledger/timing generation lack CPU clocks; managed aggregate jobs separately recorded below'),
 ('pilot_and_background_untimed_overhead','pilot and background source scripts','startup/imports/data loading/writing outside selected phase timers; no exact residual CPU inferred from sampled resource accounting')]
for stage,source,scope in unknown:row(stage,None,source,scope)
# Record all available job-level observations once per reference. They overlap
# process-clock rows above, so are deliberately never added to that subtotal.
resources={};snapshots=sorted((r/'computation_ledger/resource_snapshots').glob('*.json'))
for path in snapshots:
    snap=json.loads(path.read_text())
    for j in snap.get('ended',[])+snap.get('tracked',[]):
        if j.get('state')=='succeeded':resources[j['ref']]=dict(ref=j['ref'],note=j.get('note'),state=j['state'],reported_cpu_seconds=j.get('spend'),reported_run_seconds=j.get('ran'),source='computation_ledger/resource_snapshots/'+path.name)
subtotal=sum(z['cpu_seconds'] for z in rows if z['add_to_disjoint_process_clock_subtotal'])
latest=load('computation_ledger/resource_snapshots/final_snapshot.json')
refcpu=float(pd.read_csv(r/'reference_diagnostics.csv').cpu_seconds.sum());calls=float(pd.read_parquet(r/'run_metrics.parquet',columns=['cpu_seconds']).cpu_seconds.sum())
out=dict(status='known_and_unknown_costs_recorded',disjoint_process_clock_subtotal_cpu_seconds=subtotal,disjoint_process_clock_subtotal_cpu_hours=subtotal/3600,subtotal_is_complete_whole_study_cost=False,reason='several executed validation/correction/test/setup/postprocessing intervals were not instrumented; no missing CPU inferred from elapsed time or counts',primary_main_breakdown=dict(total_cpu_seconds=maincpu,reference_cpu_seconds=refcpu,stochastic_cpu_seconds=calls,other_process_cpu_residual_seconds=maincpu-refcpu-calls,scope='breakdown of included primary row, NOT additive extra work'),process_clock_rows=rows,resource_job_observations=list(resources.values()),resource_counter_snapshot=dict(reported_cumulative_managed_cpu_seconds=latest['used']['spend'],reported_cumulative_managed_cpu_hours=latest['used']['spend']/3600,source='computation_ledger/resource_snapshots/final_snapshot.json',scope='sampled cumulative managed-resource counter, including tracked preliminary/main/background/postprocessing jobs; excludes sandbox-only work; overlaps process-clock subtotal and can undershoot it locally; NOT an exact whole-study total'),deduplication_rules=['choose whole-job timer for primary; do not add its training/reference/call costs a second time','choose each preflight/smoke/reproduction outer timer; do not add nested calls again','initial/budget/exact/final-precision pilot files represent distinct executed phases, not alternate projections of the same timing','choose background outer cell-phase timers; do not add their internal exact/call/pilot projections or resource counters again','resource observations are keyed once by job reference, remain sampled and nonadditive; managed aggregate jobs provide recorded postprocessing CPU where no process clock exists','reserve,1.5x safety factors and per-instance extrapolations are planning quantities, excluded from all measured subtotals'],unmeasured_failed_control_costs_explicit=True)
sources=sorted({z['source'] for z in rows if (r/z['source']).is_file()}|{'computation_ledger/resource_snapshots/'+p.name for p in snapshots})
out['input_sha256']={s:hashlib.sha256((r/s).read_bytes()).hexdigest() for s in sources}
(r/'computation_ledger.json').write_text(json.dumps(out,indent=2)+'\n')
pd.DataFrame(rows).to_csv(r/'computation_ledger.csv',index=False)
print(json.dumps({k:out[k] for k in ['disjoint_process_clock_subtotal_cpu_seconds','disjoint_process_clock_subtotal_cpu_hours','subtotal_is_complete_whole_study_cost']}))
