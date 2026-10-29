"""Predict uniform-start mean cover time using fitted descriptor regression."""
import argparse
import json
from pathlib import Path
import numpy as np

parser=argparse.ArgumentParser()
for name in ['n','m','dmax','diameter']:
    parser.add_argument('--'+name,type=float,required=True)
args=parser.parse_args()
values=np.array([args.n,args.m,args.dmax,args.diameter])
if np.any(values<=0) or not 8<=args.n<=30:
    parser.error('Require positive descriptors and 8 <= n <= 30; prediction has no guarantee.')
fit=json.loads((Path(__file__).resolve().parent/'results/fitted_model.json').read_text())
z=(np.log(values)-np.array(fit['center']))/np.array(fit['scale'])
print(float(np.exp(np.r_[1,z]@np.array(fit['coefficients']))))
