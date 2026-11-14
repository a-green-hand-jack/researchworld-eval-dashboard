"""Scientific implementation checks: baseline equivalence and exact identities."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import ast,json
from pathlib import Path
import numpy as np
from methods import phi,coefficient,eb_split,all_intervals
ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(2026110201)
sl=rng.random(200);su=rng.random(2000);y=rng.binomial(1,.1+.8*sl).astype(float)
# Execute ONLY the allowed package's scalar lambda utility in isolation.
# No imports or other source code are executed.
tree=ast.parse((ROOT/'literature/ppi_mean_source.py').read_text())
node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_calc_lam_glm')
ns={'np':np,'reshape_to_2d':lambda x:np.asarray(x).reshape(len(x),-1)}
exec(compile(ast.Module(body=[node],type_ignores=[]),'official_lambda','exec'),ns)
ref=ns['_calc_lam_glm'](y,sl,su,np.eye(1),clip=False)
ours=float(2*coefficient(y,phi(sl,1),phi(su,1))[0])
# We intentionally use unbiased labeled covariance; package uses divisor n.
np.testing.assert_allclose(ours*(len(y)-1)/len(y),ref,rtol=1e-12)
# Binary scores have only one nonconstant degree of freedom, regardless of basis.
sb=rng.binomial(1,.5,size=200).astype(float);ub=rng.binomial(1,.5,size=2000).astype(float)
yb=rng.binomial(1,.1+.8*sb).astype(float)
a=all_intervals(yb,sb,ub)
np.testing.assert_allclose(a['PPI++'],a['CV3'],rtol=1e-11,atol=1e-12)
# Direct finite-support check of projection optimality and regret identity.
s=np.array([.05,.25,.55,.9]);p=np.array([.1,.3,.4,.2]);m=np.array([.1,.8,.2,.9]);rho=10/11
ph=phi(s,3);phc=ph-p@ph;mc=m-p@m
sig=phc.T@(p[:,None]*phc);c=phc.T@(p*mc)
bstar=rho*np.linalg.solve(sig,c);b=bstar+np.array([.1,-.05,.02])
vy=p@m*(1-p@m)
v=lambda bb:vy-2*bb@c+(1+1/10)*bb@sig@bb
np.testing.assert_allclose(v(b)-v(bstar),(1+1/10)*(b-bstar)@sig@(b-bstar),atol=1e-14)
np.testing.assert_allclose(c@np.linalg.solve(sig,c),p@(mc*mc),atol=1e-12)
# Inference functions are deterministic and do not mutate their fixed inputs.
copies=[x.copy() for x in [y,sl,su]]
a=all_intervals(y,sl,su);aa=all_intervals(y,sl,su)
assert a==aa
for x,z in zip([y,sl,su],copies):np.testing.assert_array_equal(x,z)
report={'checks':['official_scalar_lambda_agrees_after_declared_ddof_adjustment','binary_score_dictionary_equals_scalar','projection_regret_identity','saturated_basis_matches_conditional_mean','deterministic_and_input_immutable'],
        'seed':2026110201,'package_lambda':ref,'unbiased_covariance_lambda':ours,'passed':True}
(ROOT/'logs/verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
