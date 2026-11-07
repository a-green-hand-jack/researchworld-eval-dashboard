"""Produce measured pilot report and explicit projected production budget."""
import json
from pathlib import Path
import pandas as pd

root=Path(__file__).resolve().parents[1]
rows=[]
for stage in ['pilot','pilot_extension','pilot_memory','pilot_imbalance']:
    for path in (root/'results'/stage).glob('*.json'):
        record=json.loads(path.read_text())
        if not isinstance(record,dict) or 'cell_id' not in record:
            continue
        rows.append(dict(stage=stage,cell_id=record['cell_id'],graph=record['graph']['name'],
                         replicates=record['replicates'],wall_seconds=record['wall_seconds'],
                         cpu_seconds=record['cpu_seconds'],peak_rss_kib=record['peak_rss_kib']))
frame=pd.DataFrame(rows)
output=root/'notes';output.mkdir(exist_ok=True)
frame.to_csv(output/'pilot_timings.csv',index=False)
calibration=frame[frame.replicates==400]
if len(calibration)!=12:
    raise ValueError(f'Production-sized memory calibration incomplete ({len(calibration)}/12)')
ht=json.loads((root/'results/pilot/ht_risk_audit.json').read_text())
# Conservative cost uses the larger of measured R400 and R20 linear projection.
base=max(calibration.wall_seconds.max(),(frame.wall_seconds*400/frame.replicates).max())
mc_projection=base*102
ht_projection=max(r['wall_seconds'] for r in ht)*102*3
finalization=json.loads((root/'notes/calibration_finalization.json').read_text())
summary_measurement=finalization[-1]
raw_files=[p for name in ['pilot','pilot_extension','pilot_memory','pilot_imbalance']
           for p in (root/'results'/name).glob('*.parquet')]
raw_rows=int(sum(frame.replicates)*8*9)
raw_bytes=sum(p.stat().st_size for p in raw_files)
summary_projection=summary_measurement['wall_seconds']*2937600/raw_rows
# Reserve a further two hours for clean selected-cell reproduction, audit and integration.
full_budget=2*(mc_projection+ht_projection+summary_projection)+7200
report=dict(pilot_cells=len(frame),pilot_observed_rows=int(sum(frame.replicates)*8*9),
            timing_wall_sum_seconds=float(frame.wall_seconds.sum()),
            timing_cpu_sum_seconds=float(frame.cpu_seconds.sum()),
            measured_peak_rss_kib=int(max(frame.peak_rss_kib.max(),max(r['peak_rss_kib'] for r in ht))),
            largest_measured_R400_cell_seconds=float(calibration.wall_seconds.max()),
            projection_base_seconds_per_R400_cell=float(base),production_cells=102,
            projected_mc_seconds=float(mc_projection),projected_exact_ht_seconds=float(ht_projection),
            factor_two_budget_seconds=float(2*(mc_projection+ht_projection)),
            factor_two_budget_hours=float(2*(mc_projection+ht_projection)/3600),
            measured_raw_parquet_bytes=raw_bytes,measured_raw_rows=raw_rows,
            projected_raw_parquet_bytes=float(raw_bytes/raw_rows*2937600),
            measured_summary_wall_seconds=summary_measurement['wall_seconds'],
            measured_summary_peak_rss_kib=summary_measurement['peak_rss_kib'],
            projected_summary_seconds=float(summary_projection),
            reproduction_audit_integration_reserve_seconds=7200,
            full_analysis_budget_hours=float(full_budget/3600),
            projected_rows=2937600,projected_observed_datasets=326400,projected_prediction_datasets=326400,
            note='Conservative projections, not measurements. Exact HT max-size cost applied to every cell and three endpoint families. Scientific summarization/figure integration reserved separately. Shared-host throughput may differ.')
(output/'pilot_budget.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
