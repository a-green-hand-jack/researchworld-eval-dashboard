"""Analytic planning calculations; no model or experimental performance measurements."""
import csv, math, pathlib
root=pathlib.Path(__file__).resolve().parents[1]
with (root/'assessment/audit-precision-planning.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['audit_n','worst_case_accuracy_se','normal_95_accuracy_half_width','worst_case_paired_contrast_se','normal_95_paired_contrast_half_width'])
 for n in [256,512,1024,2048,4096]:
  w.writerow([n,0.5/math.sqrt(n),1.96*0.5/math.sqrt(n),1/math.sqrt(n),1.96/math.sqrt(n)])
with (root/'assessment/inference-cost-planning.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['candidates','search_questions','audit_questions','generated_responses','assumed_seconds_per_response','scenario_wall_hours_excluding_overhead'])
 for k,s,a in [(8,512,1024),(16,1024,1024),(16,2048,2048),(16,6016,6016)]:
  for seconds in [1,5,10]: w.writerow([k,s,a,k*(s+a),seconds,k*(s+a)*seconds/3600])
print('Wrote analytic planning tables, not measured experiment results.')
