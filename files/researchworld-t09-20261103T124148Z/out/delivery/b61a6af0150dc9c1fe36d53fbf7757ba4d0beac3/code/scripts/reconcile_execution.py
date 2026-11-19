"""Reconcile the finished study with its frozen launch and saved resource receipt."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

p=argparse.ArgumentParser();p.add_argument('--root',default='.')
a=p.parse_args();root=Path(a.root).resolve();code=root/'code' if (root/'code').exists() else root
notes=root/('analysis' if code!=root else 'notes')

def sha(file): return hashlib.sha256(file.read_bytes()).hexdigest()

def read(file): return json.loads(file.read_text())

launch=read(notes/'execution_manifest.json');audit=read(notes/'production_audit.json')
summary=read(notes/'summary_audit.json');extra=read(root/'results/diagnostics/diagnostics_manifest.json')
assert audit['complete_required'] and audit['total_rows']==2937600
assert summary['status']=='passed' and summary['scope']=='complete' and extra['status']=='complete'
ledger=pd.read_csv(notes/'cell_ledger.csv');assert len(ledger)==102 and ledger.status.eq('completed').all()
configs={name:sha(code/'configs'/name) for name in launch['configs']}
assert configs==launch['configs']
source={name:sha(code/'src/gatebench'/name) for name in launch['source_sha256']}
changed=[name for name in source if source[name]!=launch['source_sha256'][name]]
assert set(changed)<=set(['summarize.py'])
assert source['summarize.py']==summary['summary_source_sha256']
assert extra['script_sha256']==sha(code/'scripts/analyze_results.py')
assert sha(code/'scripts/audit_summaries.py')==summary['audit_source_sha256']
panels={};allfiles=[]
for stage in ['core','noise','imbalance']:
    folder=root/f'results/production_{stage}'
    raw=sorted(folder.glob('*.parquet'));metadata=[read(f.with_suffix('.json')) for f in raw]
    exact=sorted((folder/'exact_ht').glob('*.json'));risk=[r for f in exact for r in read(f)]
    assert len(raw)==audit['stages'][stage]['expected_cells']==len(exact)
    panels[stage]=dict(cells=len(raw),estimator_rows=sum(x['rows'] for x in metadata),
         raw_simulator_wall_seconds_sum=sum(x['wall_seconds'] for x in metadata),
         raw_simulator_cpu_seconds_sum=sum(x['cpu_seconds'] for x in metadata),
         exact_ht_endpoint_rows=len(risk),exact_ht_wall_seconds_sum=sum(x['wall_seconds'] for x in risk),
         exact_ht_cpu_seconds_sum=sum(x['cpu_seconds'] for x in risk),
         maximum_recorded_process_peak_rss_kib=max(x['peak_rss_kib'] for x in metadata+risk),
         raw_parquet_bytes=sum(f.stat().st_size for f in raw))
    for f in raw+exact+[f.with_suffix('.json') for f in raw]:
        allfiles.append(dict(path=str(f.relative_to(root)),sha256=sha(f),bytes=f.stat().st_size))
resource=read(notes/'resource_jobs.json')
production_runs=[x for x in resource if x['ref'] in launch['jobs']]
assert len(production_runs)==len(launch['jobs']) and all(x['state']=='succeeded' for x in production_runs)
production=dict(state='succeeded',created_at=min(x['created_at'] for x in production_runs),closed_at=max(x['closed_at'] for x in production_runs),ran=sum(x['ran'] for x in production_runs),spend=sum(x['spend'] for x in production_runs),shards=production_runs)
post=read(notes/'postprocessing_timings.json');assert len(post)==4
assert read(notes/'boundary_audit.json')['status']=='passed'
assert read(notes/'v2_dependency_audit.json')['status']=='passed'
assert read(notes/'diagnostics_audit.json')['status']=='passed'
replay=read(notes/'reproduction_audit.json')
assert replay['status']=='passed' and replay['rows']==115200
assert replay['source_sha256']==source
maximum_matched_bias=max(x['max_matched_bias'] for x in audit['stages'].values())
historical=[x for x in resource if x['ref'] not in launch['jobs']]
completed_historical=[x for x in historical if x['state']=='succeeded']
final=dict(status='completed and internally audited',planned_cells=102,completed_cells=102,
           failed_cells=0,unrun_cells=0,assignment_noise_repetitions=40800,
           mechanism_specific_datasets=326400,estimator_output_rows=2937600,
           graph_instances=36,synthetic_graph_draws=35,public_fixed_graphs=1,
           exact_ht_cell_files=102,exact_ht_endpoint_rows=306,
           launch_source_revision=launch['source_revision'],config_sha256=configs,
           frozen_launch_source_sha256=launch['source_sha256'],final_source_sha256=source,
           post_launch_source_changes=changed,
           correction_history='exposure_boundary_correction.md and roundoff_v1/ hold superseded-source provenance; corrected first-order exposures count before division. Scientific configs/graphs/seeds unchanged.',
           panel_measurements=panels,production_resource_record=production,
           other_tracked_resources=historical,
           other_completed_resource_ran_seconds_sum=sum(x.get('ran',0) for x in completed_historical),
           other_completed_resource_cpu_spend_seconds_sum=sum(x.get('spend',0) for x in completed_historical),
           production_resource_lifecycle_seconds=production['closed_at']-production['created_at'],
           resource_lifecycle_definition='Recorded resource creation to recorded completion; includes scheduling/startup/status-detection overhead, not an exact profiler of the launcher.',
           per_cell_timing_definition='Sums of actually recorded simulator or endpoint-risk function times. Excludes some graph construction, orchestration and summary work; not whole-job elapsed.',
           rss_definition='Maximum recorded process high-water RSS in raw simulation/exact-risk metadata; not an instrumented container-wide high-water mark or the later summary/audit peak.',
           postprocessing=post,replay=replay,
           boundary_audit=read(notes/'boundary_audit.json'),
           dependency_audit=read(notes/'v2_dependency_audit.json'),
           corrected_finalization_timings=read(notes/'corrected_finalization_timings.json'),
           source_environment_sha256=sha(code/'environment.json'),
           raw_and_metadata_hashes=allfiles,
           validity=dict(checkpoint_audit='production_audit.json',raw_to_summary='summary_audit.json',
                         integer_boundaries='boundary_audit.json',graph_applicability='v2_dependency_audit.json',
                         supplementary_manifest='results/diagnostics/diagnostics_manifest.json',
                         supplementary_arithmetic='diagnostics_audit.json',decomposition_check='decomposition_check.json',
                         selected_replay='reproduction_audit.json',failure_inventory='results/diagnostics/failure_inventory.csv'),
           limits=['Only four selected structural cells replayed, not a full102-cell rerun or independent implementation.',
                   'Five graph draws per synthetic regime; fixed graph/x/partition for SNAP and one-seed imbalance.',
                   'Oracle diagnostic moments and exact HT risk use simulation-known quantities.',
                   'Undefined and unsupported estimator outputs are not failed or unrun simulation cells.'])
(notes/'final_execution.json').write_text(json.dumps(final,indent=2))
launch['status']='completed; all102cells/exactHT/summaries and full internal audits passed'
launch['completion_receipt']='final_execution.json'
launch['note']='Corrected count-then-divide source/config launch hashes retained. Original pre-correction source/provenance is in roundoff_v1; no configs/graphs/seeds changed. Final source/audit/summary hashes identify the corrected execution.'
(notes/'execution_manifest.json').write_text(json.dumps(launch,indent=2))
lines=['# Completed execution reconciliation','',
'All102planned cells completed:72core,22correlated-noise and8imbalance. There are no failed/unrun cells or exclusions from the frozen matrix. All2,937,600estimator rows,306exact one-hop endpoint-family risks and complete summary/diagnostic tables are supplied. Undefined Hajek and finite unsupported spline/threshold fits remain recorded scientific estimator failures, not omitted simulation cells.','',
'Original launch/config/source authority is execution_manifest.json; final_execution.json links exact actual configs, frozen and final source hashes, all raw/metadata/exact-risk hashes, resource receipt and completed audit/replay receipts. Corrected production counts treated neighbors before dividing by degree, fixing the recorded v1 rational-boundary defect. All scientific configs/graphs/seeds are unchanged. Final source hashes identify this implementation; v1 provenance is separate.','',
'|Panel|Cells|Rows|Simulation wall s (sum)|Simulation CPU s (sum)|Exact-risk wall s (sum)|Max recorded process RSS KiB|Raw bytes|',
'|--|--:|--:|--:|--:|--:|--:|--:|']
for name,x in panels.items():
    lines.append(f"|{name}|{x['cells']}|{x['estimator_rows']}|{x['raw_simulator_wall_seconds_sum']:.2f}|{x['raw_simulator_cpu_seconds_sum']:.2f}|{x['exact_ht_wall_seconds_sum']:.2f}|{x['maximum_recorded_process_peak_rss_kib']}|{x['raw_parquet_bytes']}|")
lines += ['', 'The original v1 study was executed and superseded because of the boundary defect; it is not an unrun or scientific-negative condition. All original tracked jobs, calibration/audit/replay jobs and corrected finalization are preserved in resource_jobs.json and the historical resource fields of final_execution.json. Their runtime is additional to corrected production. The archived v1 provenance remains under roundoff_v1 and the archive branch; none of its performance values is final evidence.', '',f"Production resource lifecycle: {final['production_resource_lifecycle_seconds']:.2f}s ({final['production_resource_lifecycle_seconds']/3600:.3f}h), from its recorded creation/completion. Summed resource reported ran={production['ran']:.3f}s and CPU spend={production['spend']:.3f}s; definitions differ from lifecycle and per-function sums, so they are retained separately. Original conservative allowance7.30h was a planning estimate, not actual elapsed. The measured lifecycle includes startup/status overhead. Function timing sums exclude some graph building, launcher and summary costs; do not add them and call that the complete launcher wall time.",'',
f"Final full audit/boundary/supplementary/summary-verification timings are in postprocessing_timings.json; their stage CPU/wall and cumulative child process peak RSS are actual measurements. The corrected selected clean replay separately took{replay['wall_seconds']:.2f}s and matched115200rows/Parquet hashes exactly. It does not establish full-study independent reproduction.",'',
f'The complete source/summary hashes distinguish launch from postprocessing provenance. All three config-file byte hashes still equal launch. Full checkpoint, all40800assignment rational-boundary and raw-to-summary audits passed; analytical identities are checked in the supplied scientific tests. Maximum absolute conditional bias across all matched estimable controls is{maximum_matched_bias:.6g}. All102graph/config metadata exactly match the preserved originals; graph-only content is reusable with corrected provenance, while every empirical/exact-risk artifact is regenerated. Complete denominator/failure and claim routes are final_findings.md, results/diagnostics/claim_evidence.csv and failure_inventory.csv.','',
'No required analysis in the settled matrix remains unrun. Excluded extensions remain exclusions, not null/negative evidence. This reconciliation establishes execution and internal arithmetic checks; independent release judgement remains internal-review-repo’s role.']
(notes/'execution_reconciliation.md').write_text('\n'.join(lines)+'\n')
print(notes/'final_execution.json')
