from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
SEED=20261102
DATASETS=['german','pima','acs']
MODELS=['logistic','forest','boosting']
N_CASES=32
N_REPEATS=64
BG_SIZE=16
MULTIPLIERS=[2,8,32,128]

def seed_for(*ids):return int(np.random.SeedSequence([SEED,*ids]).generate_state(1)[0])

def exact_shap(v,d):
 from math import comb
 ids=np.arange(2**d,dtype=np.uint32)
 sizes=np.zeros(2**d,dtype=np.uint8)
 for j in range(d):sizes+=(ids>>j)&1
 weights=np.array([1/(d*comb(d-1,s)) for s in range(d)])
 phi=np.zeros(d)
 for j in range(d):
  ix=ids[(ids&(1<<j))==0]
  phi[j]=np.dot(weights[sizes[ix]],v[ix|(1<<j)]-v[ix])
 return phi

def topk(a,k=3):return np.argsort(-np.abs(a),kind='stable')[..., :k] if a.ndim==1 else np.argsort(-np.abs(a),axis=1,kind='stable')[:,:k]
