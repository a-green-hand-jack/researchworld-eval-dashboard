"""Measured timings vs explicit planning projections, never main results."""
from pathlib import Path
import json,numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1]
load=lambda f:[json.loads(line) for line in (ROOT/f).read_text().splitlines()]
initial=load('results/pilot.jsonl');budget=load('results/budget_pilot.jsonl');exact=load('results/reference_pilot.jsonl')
original_budget=list(budget);original_exact=list(exact)
precision=load('results/final_precision_pilot.jsonl') if (ROOT/'results/final_precision_pilot.jsonl').exists() else []
precision_complete=len(precision)==123
if precision_complete:
    budget=[x for x in precision if x['kind']=='estimator']
    exact=[x for x in precision if x['kind']=='reference' and x['dataset']=='german']
if {r['model'] for r in exact}!={'logistic','forest','histboost'}:raise ValueError('exact pilot unfinished')
cfg=json.loads((ROOT/'configs/main-proposal.json').read_text());n=cfg['n_instances'];r=cfg['n_repeats']
rows=[]
for d in cfg['datasets']:
 for m in cfg['models']:
  timing=[x for x in budget if x['dataset']==d and x['model']==m]
  stochastic_cpu=sum(np.mean([x['cpu_seconds'] for x in timing if x['estimator']==e and x['budget']==b]) for e in cfg['estimators'] for b in cfg['budgets'][d])*n*r
  stochastic_wall=sum(np.mean([x['wall_seconds'] for x in timing if x['estimator']==e and x['budget']==b]) for e in cfg['estimators'] for b in cfg['budgets'][d])*n*r
  references=([x for x in exact if x['model']==m] if d=='german' else [x for x in (precision if precision_complete else initial) if x['dataset']==d and x['model']==m and x['kind']=='reference'])
  refcpu=float(np.mean([x['cpu_seconds'] for x in references]));refwall=float(np.mean([x['wall_seconds'] for x in references]))
  info=next(x['info'] for x in initial if x['dataset']==d and x['model']==m and x['kind']=='model')
  rows.append(dict(dataset=d,model=m,n_instances=n,n_repeats=r,n_stochastic_calls=n*r*len(cfg['estimators'])*len(cfg['budgets'][d]),n_features=info['n_features'],background_size=info['background_size'],observed_reference_cpu_seconds=refcpu,observed_reference_wall_seconds=refwall,reference_timing_inputs=len(references),reference_prediction_rows=references[0]['prediction_rows'],observed_training_cpu_seconds=info['train_cpu_seconds'],projected_stochastic_cpu_hours=stochastic_cpu/3600,projected_reference_cpu_hours=refcpu*n/3600,projected_total_cpu_hours=(stochastic_cpu+refcpu*n+info['train_cpu_seconds'])/3600,projected_serial_wall_hours=(stochastic_wall+refwall*n+info['train_wall_seconds'])/3600))
frame=pd.DataFrame(rows);frame.to_csv(ROOT/'results/pilot_cost_projection.csv',index=False)
observed_pilot_cpu=sum(x.get('cpu_seconds',x.get('info',{}).get('train_cpu_seconds',0)) for x in initial+original_budget+original_exact+precision)
planned=float(frame['projected_total_cpu_hours'].sum());report=dict(kind='planning_projection_from_actual_pilot_not_main_result',timing_source='final_float64_adapter' if precision_complete else 'initial_float32_adapter',main_cpu_hours_point_projection=planned,observed_timed_pilot_cpu_hours=observed_pilot_cpu/3600,main_cpu_hours_with_1p5_safety_factor=planned*1.5,setup_aggregation_background_sensitivity_reserve_cpu_hours=2,total_including_safety_pilot_and_reserve_cpu_hours=planned*1.5+observed_pilot_cpu/3600+2,approximate_planning_target_cpu_hours=24,notes=['two pilot inputs per stochastic cell; one exact German input/model, so timing spread is uncertain','all three main stochastic budgets explicitly measured','1.5x main safety factor and 2 CPU-hour reserve are planning allowances, not measurements','main model/background fixed; 32 background rows; exact reference all 2^d coalitions','no main-data adequacy claim follows from this pilot'])
(ROOT/'results/pilot_cost_projection.json').write_text(json.dumps(report,indent=2)+'\n')
print(frame.to_string(index=False));print(json.dumps(report,indent=2))
