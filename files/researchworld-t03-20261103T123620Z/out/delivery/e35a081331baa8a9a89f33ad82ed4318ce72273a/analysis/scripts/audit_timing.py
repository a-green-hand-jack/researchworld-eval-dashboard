"""Preserve and flag observed elapsed/process-time disagreement; no trimming."""
import argparse,json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--input',default='results');a=p.parse_args();r=ROOT/a.input
runs=pd.read_parquet(r/'run_metrics.parquet');refs=pd.read_csv(r/'reference_diagnostics.csv');jobs=pd.read_csv(r/'job_costs.csv')
rows=[]
for scope,g in [('stochastic_calls',runs),('exact_references',refs)]:
    ratio=g.wall_seconds/g.cpu_seconds.clip(lower=1e-9)
    flagged=(g.wall_seconds>1)&(ratio>10)
    rows.append(dict(scope=scope,n_records=len(g),sum_cpu_seconds=float(g.cpu_seconds.sum()),sum_wall_seconds=float(g.wall_seconds.sum()),n_wall_gt_1s_and_gt_10x_cpu=int(flagged.sum()),largest_wall_records=json.loads(g.nlargest(5,'wall_seconds').to_json(orient='records'))))
out=dict(status='complete',policy='all raw wall measurements retained without winsorizing or deletion; CPU is primary efficiency currency alongside actual model rows',interpretation='wall clocks include shared-host scheduling and any process/world suspension; two exact-reference wall measurements exceed 162000 seconds despite under 180 CPU seconds each; no inference of model-computation slowdown from those records',records=rows,whole_jobs_process_cpu_seconds=float(jobs.process_total_cpu_seconds.sum()),whole_job_wall_scope='individual cell clocks overlap and include interruptions; do not sum as elapsed study time or clean deployment latency')
(r/'timing_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({x['scope']:x['n_wall_gt_1s_and_gt_10x_cpu'] for x in rows}))
