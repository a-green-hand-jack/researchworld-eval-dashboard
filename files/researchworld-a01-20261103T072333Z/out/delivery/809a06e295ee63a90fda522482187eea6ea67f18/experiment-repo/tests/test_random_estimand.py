"""Regression for fixed-cohort censoring versus reachable-only success probability."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import pandas as pd
from summarize import random_summary
from analysis import random_baseline,context,patterns,winning_patterns

# Six tasks: a target at 0 cannot beat a .9 rival with alpha=.1, even at full budget.
X=np.array([[0.]*6,[.9]*6]);u=np.full(6,.1)
assert not winning_patterns(X,0,u,'mean',context(X,'mean'),patterns(6)).any()
p,expectation,reps=random_baseline(X,0,u,'mean',context(X,'mean'),6,np.random.default_rng(1),1)
assert p==0 and expectation==7 and reps==0
# One exact infeasible target plus a reachable target: preserve both in stopping mean.
g=pd.DataFrame({'random_success_at_k':[.5,np.nan], 'random_expected_censored_k':[2.,expectation]})
r=random_summary(g)
assert r['random_expected_censored_k']==4.5 and r['random_expected_censored_k_n']==2
assert r['random_success_at_optimum_reachable']==.5 and r['random_success_at_optimum_n']==1
print('Passed exhaustive infeasibility and two-target denominator regression')
