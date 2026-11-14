"""Prospective affine wall quote; observed envelopes are not future guarantees."""
import json
from pathlib import Path


def affine_prefix_quote(root,runs,excluded,slope,startup_cpu_s,contingency=1.5):
    if slope<1.25 or contingency<1.5:
        raise ValueError('Required slope floor/remaining-work contingency')
    observations=[]
    for run in runs:
        if run['name'] in excluded:
            continue
        directory=Path(root)/'results/confirmatory'/run['name']
        for path in sorted(directory.glob('curve*.jsonl')):
            text=path.read_text();lines=text.splitlines()
            for index,line in enumerate(lines):
                try:
                    row=json.loads(line)
                except json.JSONDecodeError:
                    if index==len(lines)-1 and not text.endswith('\n'):
                        continue
                    raise
                observations.append(dict(run=run['name'],path=str(path.relative_to(root)),
                    line=index+1,step=row['step'],cpu_s=row['cpu_s'],wall_s=row['elapsed_s']))
        summary=directory/'summary.json'
        if summary.exists():
            row=json.loads(summary.read_text())
            observations.append(dict(run=run['name'],path=str(summary.relative_to(root)),
                step=row['final']['step'],cpu_s=row['cpu_s'],wall_s=row['elapsed_s']))
        attempts=directory/'attempts.jsonl'
        if attempts.exists():
            for index,line in enumerate(attempts.read_text().splitlines()):
                row=json.loads(line)
                if 'segment_cpu_s' in row and 'segment_wall_s' in row:
                    observations.append(dict(run=run['name'],path=str(attempts.relative_to(root)),
                        line=index+1,step=row.get('end_step'),cpu_s=row['segment_cpu_s'],wall_s=row['segment_wall_s']))
    for row in observations:
        if row['cpu_s']<0 or row['wall_s']<0:
            raise ValueError('Negative measured clock')
    excess_source=max(observations,key=lambda r:r['wall_s']-slope*r['cpu_s'],default=None)
    excess=max(0.,excess_source['wall_s']-slope*excess_source['cpu_s']) if excess_source else 0.
    ratio_source=max((r for r in observations if r['cpu_s']>0),key=lambda r:r['wall_s']/r['cpu_s'],default=None)
    remaining=[r for r in runs if r['status']!='completed']
    # Full price even for interrupted/active runs: no assumed checkpoint savings.
    cpu=sum(r['repriced_full_cpu_s'] for r in remaining)
    return dict(model='elapsed_prefix_affine_v1',slope_wall_per_cpu=slope,
        max_positive_elapsed_excess_s=excess,excess_source=excess_source,
        measured_prefixes_and_ends=len(observations),
        max_recorded_positive_cpu_wall_ratio=(ratio_source['wall_s']/ratio_source['cpu_s'] if ratio_source else None),
        max_ratio_source=ratio_source,
        positive_elapsed_zero_cpu_observations=sum(r['wall_s']>0 and r['cpu_s']==0 for r in observations),
        remaining_configurations=len(remaining),remaining_full_config_cpu_s=cpu,
        startup_cpu_s=startup_cpu_s,remaining_contingency=contingency,
        reserved_wall_hours=contingency*(slope*(cpu+startup_cpu_s)+len(remaining)*excess)/3600,
        reserved_remaining_cpu_hours=contingency*(cpu+startup_cpu_s)/3600,
        excluded_historical_runs=sorted(excluded),
        clock_rule='All main/discarded curve prefixes,completed ends and recorded attempt ends enter;only the two explicitly authorized historical runs are excluded.Raw ratios and failed guards remain.No later averaging erases an earlier positive excess.',
        limitation='Prospective observed affine envelope plus50%reserve,not a future-stall guarantee.Every remaining configuration receives the largest observed additive excess;new excesses reprice the entire remainder and can stop work.')
