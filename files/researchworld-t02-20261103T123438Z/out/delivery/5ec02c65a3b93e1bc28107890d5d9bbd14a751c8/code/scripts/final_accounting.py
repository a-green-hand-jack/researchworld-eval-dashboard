"""Reconcile retained clocks without adding overlapping platform and run totals."""
import argparse,json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser()
p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
a=p.parse_args();root=a.root
load=lambda path:json.loads((root/path).read_text())
resource=load('reproduction/checkpoints/final204-resources.json')
status=load('reproduction/checkpoints/final204-resource-status.json')
registry=load('configs/confirmatory.json')['runs']
summaries=[load('results/confirmatory/'+r['name']+'/summary.json') for r in registry]
ends=[];unknown=[];groups=defaultdict(list)
for r,s in zip(registry,summaries):
    events=[json.loads(x) for x in (root/'results/confirmatory'/r['name']/'attempts.jsonl').read_text().splitlines()]
    done={x['attempt_id'] for x in events if x.get('event')=='ended'}
    unknown += [dict(name=r['name'],**x) for x in events if x.get('event')=='started' and x['attempt_id'] not in done]
    ends += [dict(name=r['name'],**x) for x in events if x.get('event')=='ended']
    groups[(r['family'],r['width'])].append(s)
known=resource['production_observed_cpu_s_lower_bound']+resource['measured_preproduction_cpu_s']+resource['additional_known_derived_tooling_cpu_s']+resource['additional_known_software_tooling_cpu_s']
assert len(summaries)==len(ends)==204
runtime=[]
for (family,width),values in sorted(groups.items()):
    row=dict(family=family,width=width,n=len(values))
    for key in ['cpu_s','elapsed_s']:
        v=[x[key] for x in values]
        row[key]=dict(min=min(v),median=float(np.median(v)),max=max(v),sum=sum(v))
    runtime.append(row)
report=dict(generated_utc=datetime.now(timezone.utc).isoformat(),kind='Final recorded-component resource reconciliation; overlapping clocks remain separate',completed_registered_runs=204,unstarted_or_incomplete_runs=0,completed_end_records=len(ends),unmatched_attempt_starts=unknown,last_registered_attempt_ended_utc=max(x['ended_utc'] for x in ends),production_summary_cpu_s_lower_bound=resource['production_observed_cpu_s_lower_bound'],production_summary_elapsed_s=sum(x['elapsed_s'] for x in summaries),preproduction_known_cpu_s=resource['measured_preproduction_cpu_s'],timed_derived_child_plus_wrapper_cpu_s=resource['additional_known_derived_tooling_cpu_s'],timed_software_cpu_s=resource['additional_known_software_tooling_cpu_s'],known_disjoint_components_cpu_s_lower_bound=known,known_disjoint_components_cpu_hours_lower_bound=known/3600,platform_aggregate_spend_separate=status['used'],final_pipeline=load('reproduction/derived-timing/final204.json'),actual_summary_runtime_by_cell=runtime,remaining_registered_training=0,cap_cpu_hours=44,original_deadline_missed=True,revised_training_cutoff_utc='2026-11-08T00:09:10.373000+00:00',revised_package_cutoff_utc='2026-11-08T00:39:10.373000+00:00',note='No future startup/final-tooling allowance is an actual cost. Generic monitor retains historical projections and residual startup reserve even when remaining registered work is zero; these are not remaining training. Summary CPU retains measured discarded prefix plus resumed work, but unknown tail and unmetered sandbox/import/transfer/guard/check costs prevent an exhaustive exact total. Platform aggregate overlaps these clocks and is not added. Summed run elapsed can overlap concurrent jobs and preserves historic huge low-CPU gaps; it is not project wall time.')
(root/'reproduction/final-resource-accounting.json').write_text(json.dumps(report,indent=2)+'\n')
print('Known component CPUh lower bound',known/3600,'; platform aggregate is separate')
