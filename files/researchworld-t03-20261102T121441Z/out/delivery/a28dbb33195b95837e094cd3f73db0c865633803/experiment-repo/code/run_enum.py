"""Exact full-enumeration targets (2^d coalitions) for the first --n instances of a model whose target is not structural
(German MLP, d=20). Adds `phi_enum` [n,d] to results/<ds>/targets/<model>.npz (prefix of the interleaved instance list).
Usage: python code/run_enum.py --ds german --model mlp --n 20
"""
import argparse, os, sys, time, json, warnings
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

ap = argparse.ArgumentParser()
ap.add_argument("--ds", required=True); ap.add_argument("--model", required=True)
ap.add_argument("--n", type=int, default=20); ap.add_argument("--K", type=int, default=50)
a = ap.parse_args()
out = os.path.join(common.ROOT, "results", a.ds)
tp = os.path.join(out, "targets", f"{a.model}.npz")
z = dict(np.load(tp))
T = common.Task(a.ds, a.model, K=a.K)
pos = np.array(json.load(open(os.path.join(out, "instances.json")))["test_positions"])[: a.n]
X = T.Xte[pos]
part = os.path.join(out, "targets", f"{a.model}_enum_partial.npz")
done = list(np.load(part)["phi"]) if os.path.exists(part) else []
t0 = time.time()
for i in range(len(done), len(X)):
    phi, fx, f0 = common.exact_enum(T.f, T.bg, X[i])
    assert abs(phi.sum() - (fx - f0)) < 1e-6, "efficiency violated"
    done.append(phi); np.savez(part, phi=np.array(done))
    print(f"  [{a.ds}/{a.model}] enum instance {i+1}/{len(X)} {time.time()-t0:.0f}s", flush=True)
z["phi_enum"] = np.array(done)
np.savez(tp, **z)
print(f"HUTIAN_WAKE: done enum {a.ds}/{a.model} n={len(done)}", flush=True)
