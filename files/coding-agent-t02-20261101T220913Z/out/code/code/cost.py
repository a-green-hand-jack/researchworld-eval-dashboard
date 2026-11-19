"""Sum per-run wall time (core-hours) per experiment -> tables/cost_core_hours.json"""
import json, os
out = {}
for d in ['e1_width', 'e2_clock', 'e3_capacity', 'e4_arch', 'e5_rescale', 'e6_ops', 'pilot2']:
    out[d] = round(sum(json.load(open(f'/work/results/{d}/{f}'))['wall'] for f in os.listdir(f'/work/results/{d}') if f.endswith('.json')) / 3600, 1)
json.dump(out, open('/work/tables/cost_core_hours.json', 'w'), indent=1); print(out, sum(out.values()))
