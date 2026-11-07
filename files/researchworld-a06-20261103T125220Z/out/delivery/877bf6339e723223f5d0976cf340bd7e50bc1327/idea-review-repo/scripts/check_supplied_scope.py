"""Check supplied resource arithmetic; does not run or repeat LLM analysis."""
import json,math,pathlib,datetime
root=pathlib.Path(__file__).resolve().parents[1]
p=root/'provenance/scope-gate-inputs'
s=json.loads((p/'real-scope.json').read_text());summary=json.loads((p/'pilot-summary.json').read_text())
raw=[json.loads(line) for line in (p/'pilot-responses.jsonl').read_text().splitlines()]
mean=sum(r['wall_seconds'] for r in raw)/len(raw)
assert len(raw)==100==summary['n_responses']
assert len({r['question_id'] for r in raw})==25==summary['n_questions']
assert abs(mean-summary['wall_per_response']['mean'])<1e-10
calls=len(s['active_candidate_ids'])*(s['search_questions']+s['audit_questions'])
assert calls==12288==s['actual_planned_main_responses']
t=s['timing_planning'];nominal=calls*t['predicted_mean_seconds']/3600
forecast=nominal*t['contingency_factor']+t['reserved_downstream_hours']+t['additional_overhead_allowance_hours']
assert abs(forecast-t['total_forecast_including_reserve_hours'])<1e-10
peak=s['memory_measured_peak_kb']/1024**2
assert peak<4
N=s['fresh_target']['unseen_population_questions'];m=s['audit_questions']
se=math.sqrt((N-m)/(N-1))/(2*math.sqrt(m))
result={'classification':'verification of supplied measurements and planning arithmetic; not new experimental evidence','pilot_responses':len(raw),'pilot_questions':25,'measured_mean_response_wall_seconds':mean,'measured_peak_gib':peak,'memory_headroom_gib':4-peak,'planned_main_responses':calls,'planning_generation_hours':nominal,'planning_twofold_generation_plus_48h_reserve_plus_2h_overhead_hours':forecast,'planning_audit_finite_population_se':se,'planning_normal_95_audit_half_width':1.96*se,'frozen_week_deadline':s['time_gate']['deadline_utc'],'forecast_margin_hours_at_scope_freeze':s['time_gate']['remaining_hours_at_freeze']-forecast,'gate':'go for the exact frozen Tier B; not approval of later claims or release'}
(root/'assessment/scope-gate-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
