import sys, argparse, json; sys.path.insert(0, __file__.rsplit("/scripts", 1)[0])
from shapaudit import cells
ap = argparse.ArgumentParser()
ap.add_argument("--dataset"); ap.add_argument("--d_sub", type=int, default=None); ap.add_argument("--model"); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--n_inst", type=int, default=cells.N_INST); ap.add_argument("--output", default="prob"); ap.add_argument("--m", type=int, default=cells.M_BG)
a = ap.parse_args()
print(json.dumps(cells.build(a.dataset, a.d_sub, a.model, a.seed, a.m, a.n_inst, output=a.output), indent=1))
