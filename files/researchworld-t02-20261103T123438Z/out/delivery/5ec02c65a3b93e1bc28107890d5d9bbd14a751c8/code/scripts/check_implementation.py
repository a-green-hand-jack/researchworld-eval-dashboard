"""Independent invariants for arithmetic, gather equivalence and Fourier diagnostic."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import torch
from torch import nn
torch.set_num_threads(1)
from train import PairMLP, dataset, spectral_fraction
p = 7
x,y,tr,va,digest = dataset(p,.4,123,'add')
assert len(set(tr.tolist()) & set(va.tolist())) == 0
assert sorted(tr.tolist()+va.tolist()) == list(range(p*p))
assert torch.equal(y,(x[:,0]+x[:,1])%p)
assert digest == dataset(p,.4,123,'add')[-1]
model = PairMLP(p,13,'relu')
one_hot = torch.cat([nn.functional.one_hot(x[:,0],p),nn.functional.one_hot(x[:,1],p)],1).float()
reference = model.output(torch.relu(nn.functional.linear(one_hot,model.input_weight,model.input_bias)))
assert torch.allclose(model(x),reference,atol=1e-7)
loss_a = model(x).square().sum()
grad_a = torch.autograd.grad(loss_a,tuple(model.parameters()))
loss_b = reference.square().sum()
grad_b = torch.autograd.grad(loss_b,tuple(model.parameters()))
assert all(torch.allclose(a,b,atol=1e-5,rtol=1e-5) for a,b in zip(grad_a,grad_b))
a,b,c = np.meshgrid(np.arange(p),np.arange(p),np.arange(p),indexing='ij')
correct = torch.tensor(np.cos(2*np.pi*(a+b-c)/p).reshape(p*p,p))
assert abs(spectral_fraction(correct,p,'add')-1.) < 1e-10
wrong = torch.tensor(np.cos(2*np.pi*(2*a+b-c)/p).reshape(p*p,p))
assert spectral_fraction(wrong,p,'add') < 1e-20
print('PASS: exact arithmetic, disjoint reproducible split, forward/gradient equivalence, Fourier template')
