"""Measured pilot diagnostics and cost planning; forecasts are not measurements."""
import json,pathlib
import numpy as np
import pandas as pd
pilot=pd.read_json('results/real-pilot-scope.jsonl',lines=True)
usage=pilot.usage.apply(pd.Series)
# Use nonnegative least squares for overhead/input/output cost extrapolation.
from scipy.optimize import nnls
features=np.c_[np.ones(len(pilot)),pilot.input_tokens,usage.completion_tokens]
coefficients,_=nnls(features,pilot.wall_seconds.to_numpy())
result=dict(measured=dict(responses=len(pilot),questions=int(pilot.question_id.nunique()),wall_mean=float(pilot.wall_seconds.mean()),wall_p95=float(pilot.wall_seconds.quantile(.95)),wall_max=float(pilot.wall_seconds.max()),cpu_mean=float(pilot.cpu_seconds.mean()),prompt_tokens_total=int(usage.prompt_tokens.sum()),completion_tokens_total=int(usage.completion_tokens.sum()),invalid_format=int(pilot.invalid_format.sum()),out_of_range=int(pilot.out_of_range.sum()),length_endings=int((pilot.finish_reason=='length').sum()),completion_tokens_above_requested_cap=int((usage.completion_tokens>8).sum())),timing_fit=dict(nonnegative_seconds_intercept=float(coefficients[0]),seconds_per_input_token=float(coefficients[1]),seconds_per_completion_token=float(coefficients[2]),warning='Planning regression on validation runtime only, with nonnegative coefficients; not a guaranteed throughput rate.'))
census=pathlib.Path('results/main-prompt-token-census.csv.gz')
if census.exists():
 x=pd.read_csv(census);mean_tokens=float(x.input_tokens.mean());pred=float(np.array([1,mean_tokens,usage.completion_tokens.mean()])@coefficients)
 result['planning']=dict(main_census_mean_input_tokens=mean_tokens,main_census_max_input_tokens=int(x.input_tokens.max()),validation_mean_input_tokens=float(pilot.input_tokens.mean()),predicted_mean_seconds=max(float(pilot.wall_seconds.mean()),pred),contingency_factor=2.,reserved_downstream_hours=48.,A_calls=32768,B_calls=12288,C_calls=3072)
 for tier,calls in [('A',32768),('B',12288),('C',3072)]:result['planning'][tier+'_twofold_generation_plus_reserve_hours']=2*calls*result['planning']['predicted_mean_seconds']/3600+48
pathlib.Path('results/real-pilot-scope.diagnostics.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
