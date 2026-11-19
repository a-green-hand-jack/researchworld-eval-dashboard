import sys, argparse, json; sys.path.insert(0, __file__.rsplit("/scripts", 1)[0])
from shapaudit import cells
ap = argparse.ArgumentParser()
ap.add_argument("--dataset"); ap.add_argument("--d_sub", type=int, default=None); ap.add_argument("--model", default="gbdt"); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--n_inst", type=int, default=30); ap.add_argument("--m", type=int, default=cells.M_BG)
a = ap.parse_args()
print(json.dumps(cells.build_live(a.dataset, a.d_sub, a.model, a.seed, a.m, a.n_inst), indent=1))
