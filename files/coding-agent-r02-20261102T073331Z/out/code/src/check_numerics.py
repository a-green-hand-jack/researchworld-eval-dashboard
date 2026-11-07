"""Higher-precision volume check and reproduction of the unchanged initial methods."""
import itertools, json, time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.integrate import quad
from core import generate, Calibrator, center, SCENARIOS
from run_experiments import volume

ROOT=Path(__file__).resolve().parents[1]
start=time.perf_counter()
old=pd.read_csv(ROOT/'results/initial/runs.csv')
new=pd.read_csv(ROOT/'results/runs.csv')
keys=['scenario','k','rep','method']
common=['coverage','g0','g1','boundary','interior','v1','v2','clr_infinite']
joined=old.merge(new,on=keys,suffixes=('_old','_new'),validate='one_to_one')
maxdiff={x:float(np.nanmax(np.abs(joined[x+'_old']-joined[x+'_new']))) for x in common}
assert max(maxdiff.values())==0

records=[]; analytic=[]
for sc in ['dense','hetero','zeros','mixed']:
    sid=list(SCENARIOS).index(sc)
    for rep in range(10):
        seeds=np.random.SeedSequence([20261102,sid,3,rep]).spawn(4)
        pilot=generate(np.random.default_rng(seeds[0]),1000,3,sc)
        cal=generate(np.random.default_rng(seeds[1]),499,3,sc)
        c=Calibrator.fit(pilot,cal,scenario=sc)
        v=volume(c,sc,int(seeds[3].generate_state(1)[0]),power=18)
        low=new[(new.scenario==sc)&(new.k==3)&(new.rep==rep)].set_index('method')
        for method in v:
            for j,metric in enumerate(['v2','v1']):
                records.append(dict(scenario=sc,rep=rep,method=method,metric=metric,
                                    low=low.loc[method,metric],high=v[method][j],
                                    difference=v[method][j]-low.loc[method,metric]))
        if rep==0:
            q=c.thresholds['Max']
            def exact_volume(x):
                m=center(np.array([x]),3)[0]
                lo=np.maximum(0,m-q);hi=np.minimum(1,m+q);width=hi-lo
                t=1-lo.sum()
                return sum((-1)**len(sub)*max(t-sum(width[j] for j in sub),0.)**2
                           for r in range(4) for sub in itertools.combinations(range(3),r))
            exact,error=quad(exact_volume,-1,1,epsabs=1e-10,limit=200)
            analytic.append(dict(scenario=sc,q=q,analytic=exact/2,
                                 sobol=v['Max'][0],difference=v['Max'][0]-exact/2,
                                 quadrature_error=error/2))
checks=pd.DataFrame(records);checks.to_csv(ROOT/'results/integration_check.csv',index=False)
pd.DataFrame(analytic).to_csv(ROOT/'results/analytic_volume_check.csv',index=False)
meta=dict(initial_methods_max_absolute_difference=maxdiff,
          max_absolute_individual_volume_difference=float(checks.difference.abs().max()),
          max_absolute_mean_volume_difference=float(checks.groupby(['scenario','method','metric']).difference.mean().abs().max()),
          max_analytic_sobol_difference=float(max(abs(a['difference']) for a in analytic)),
          elapsed_seconds=time.perf_counter()-start,n_cells=40,high_power=18)
(ROOT/'results/numerical_checks.json').write_text(json.dumps(meta,indent=2)+'\n')
(ROOT/'paper/generated/check_numbers.tex').write_text(
    '\\newcommand{\\MaxIntegrationMeanDiff}{'+f"{meta['max_absolute_mean_volume_difference']:.4f}"+'}\n'+
    '\\newcommand{\\MaxIntegrationSingleDiff}{'+f"{meta['max_absolute_individual_volume_difference']:.4f}"+'}\n'+
    '\\newcommand{\\MaxAnalyticDiff}{'+f"{meta['max_analytic_sobol_difference']:.5f}"+'}\n'+
    '\\newcommand{\\CheckSeconds}{'+f"{meta['elapsed_seconds']:.1f}"+'}\n')
print(json.dumps(meta,indent=2))
