"""Exploratory fixed-answer-budget policy comparison, explicitly separate from frozen grid.
768 correctness evaluations: 8*96 selection-only vs 8*64+2*128 audit policy.
Each policy targets its own selected winner; not a same-winner comparison.
"""
import json,pathlib
import numpy as np
import pandas as pd
from scipy.stats import norm
from statistics import evaluate
from run_experiments import sid,summary,R
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts'
def main():
    key='8_0.5_0_0.7';rng=np.random.default_rng(1101+sid(key));Z=np.sqrt(.5)*rng.normal(size=(R,256,1))+np.sqrt(.5)*rng.normal(size=(R,256,8));X=(Z<=norm.ppf(.7)).astype(float)
    Y=np.load(ROOT/'data/outcomes.npy');perm=np.array([np.random.default_rng(3301+i).permutation(len(Y)) for i in range(R)])
    rows=[]
    for domain,T,N in [('iid_population',X,None),('real_cache',Y,len(Y))]:
      for n in [64,96]:
        if N is None:S=T[:,:n];A=T[:,n:n+128];truth=np.full(8,.7);total=None
        else:S=T[perm[:,:n]];A=T[perm[:,n:n+128]];truth=T.mean(0);total=T.sum(0)
        res,ci=evaluate(S,A,truth,np.random.default_rng(8801),N=N,total_success=total)
        for row in summary({'domain':domain,'n':n,'K':8,'m':128,'answer_budget':768},res,ci):
          if (n==64 and row['method']=='Audit-exact') or (n==96 and row['method'] in ['Naive-Wilson','Simult-Hoeffding','Multiplier']):
            row['selected_true_accuracy']=float(res['target'].mean());rows.append(row)
    df=pd.DataFrame(rows);df.to_csv(OUT/'budget_matched.csv',index=False)
    lines=['\\begin{tabular}{llrrrr}','\\toprule','Domain & Policy & $n$ & Coverage (\\%) & Width (pp) & Winner truth (\\%) \\\\','\\midrule']
    for r in rows:lines.append(f"{r['domain'].replace('_',' ')} & {r['method']} & {r['n']} & {100*r['coverage']:.2f} & {100*r['mean_width']:.2f} & {100*r['selected_true_accuracy']:.2f} \\\\")
    lines+=['\\bottomrule','\\end{tabular}'];(OUT/'tables/budget.tex').write_text('\n'.join(lines));print(df[['domain','n','method','coverage','mean_width','selected_true_accuracy']].to_string(index=False))
if __name__=='__main__':main()
