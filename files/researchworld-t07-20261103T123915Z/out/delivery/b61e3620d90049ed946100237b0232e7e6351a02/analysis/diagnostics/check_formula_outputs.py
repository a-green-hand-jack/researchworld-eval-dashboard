"""Check reconstructed alpha10 paper scores against actual primary alpha10 cells."""
import json,pathlib
import numpy as np,pandas as pd
root=pathlib.Path(__file__).resolve().parents[1];out=root/'results/study'
formula=pd.read_parquet(out/'aipw_formula_predictions.parquet');counts=0;cells=0;maxdiff=0.
for path in (out/'development').glob('*/*.json'):
 d=json.loads(path.read_text());budgets=[int(k) for k,v in d['selection'].items() if v['parameters']['aipw_paper']==10.]
 if not budgets:continue
 df=pd.read_parquet(out/'predictions'/d['benchmark']/f"{d['scenario']}.parquet")
 paper=df[(df.method=='aipw_paper')&df.budget.isin(budgets)][['budget','repeat','target_row','predicted_score']]
 f=formula[(formula.benchmark==d['benchmark'])&(formula.scenario==d['scenario'])&formula.budget.isin(budgets)]
 joined=paper.merge(f,on=['budget','repeat','target_row'],validate='one_to_one');assert len(joined)==len(paper)
 delta=np.abs(joined.predicted_score-joined.paper_alpha10_score);assert delta.max()<=1e-12
 counts+=len(joined);cells+=20*len(budgets);maxdiff=max(maxdiff,float(delta.max()))
record={'target_predictions_checked':counts,'benchmark_scenario_budget_draw_cells_checked':cells,'max_abs_direct_primary_alpha10_minus_reconstruction':maxdiff,'tolerance':1e-12,'passed':True,
 'purpose':'Direct primary fits with preselected alpha10 agree with separate same-alpha reconstruction; no new fitting or observations'}
(out/'aipw_formula_integrity.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');print(json.dumps(record))
