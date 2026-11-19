"""Reproduce planning arithmetic from supplied resource metadata; no outcomes read."""
import datetime as dt
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
inputs = ROOT / 'provenance/fallback-gate-inputs'
job = json.loads((inputs / 'shard0-resource.json').read_text())
clock = json.loads((inputs / 'assessment-time.json').read_text())
scope = json.loads((inputs / 'original-scope.json').read_text())
# Resource retains a truncated terminal-summary suffix, not the full raw cache.
# Extract only explicit count/timing fields present in that suffix.
summary = {}
for key in ['added_responses', 'total_responses', 'wall_seconds', 'cpu_seconds']:
    match = re.search(r'"' + key + r'":\s*([0-9.]+)', job['output'])
    assert match, key
    summary[key] = float(match.group(1))
assert summary['added_responses'] == summary['total_responses'] == 6144
assert scope['stopping_rule'].find('first 4 frozen-prefix candidates') >= 0
assert scope['active_candidate_ids'][:4] == [0, 10, 14, 13]
now = dt.datetime.fromisoformat(clock['assessed_utc'])
deadline = dt.datetime.fromisoformat(clock['deadline_utc'])
remaining = (deadline - now).total_seconds() / 3600
elapsed = summary['wall_seconds'] / 3600
cpu = summary['cpu_seconds'] / 3600
active = job['ran'] / 3600
reserve = clock['downstream_reserve_hours']
overhead = clock['overhead_allowance_hours']
N = 12032 - 256
m = 512
se = math.sqrt((N - m) / (N - 1) / (4 * m))
output = dict(
    assessed_utc=clock['assessed_utc'], deadline_utc=clock['deadline_utc'],
    remaining_hours=remaining,
    supplied_shard_elapsed_hours=elapsed, supplied_shard_cpu_hours=cpu,
    supplied_resource_active_hours=active,
    continue_B_twofold_elapsed_plus_reserve_hours=2 * elapsed + reserve + overhead,
    continue_B_passes_elapsed_gate=2 * elapsed + reserve + overhead <= remaining,
    no_more_inference_margin_after_reserve_and_overhead_hours=remaining-reserve-overhead,
    fallback_search_questions=256, fallback_audit_questions=m,
    fallback_candidates=[0, 10, 14, 13], analyzed_response_pairs=4*(256+m),
    actually_generated_main_responses=summary['total_responses'],
    generated_pairs_outside_analysis=summary['total_responses']-4*(256+m),
    fresh_target_questions=N,
    finite_audit_worst_case_planning_se=se,
    approximate_normal_95_half_width_percentage_points=1.96*se*100,
    planning_only='Normal half-width is not an exact observed interval; active/CPU clocks do not replace elapsed deadline cost.',
)
assert not output['continue_B_passes_elapsed_gate']
assert output['no_more_inference_margin_after_reserve_and_overhead_hours'] > 0
print(json.dumps(output, indent=2))
