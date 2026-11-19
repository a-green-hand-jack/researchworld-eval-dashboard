import sys, argparse; sys.path.insert(0, __file__.rsplit("/scripts", 1)[0])
from shapaudit import yardstick
ap = argparse.ArgumentParser()
ap.add_argument("--dataset"); ap.add_argument("--d_sub", type=int, default=None); ap.add_argument("--model"); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--n_bg", type=int, default=10); ap.add_argument("--n_seed", type=int, default=12); ap.add_argument("--n_boot", type=int, default=10); ap.add_argument("--n_inst", type=int, default=30)
a = ap.parse_args()
for variant, n, base in (("bg", a.n_bg, 0), ("seed", a.n_seed, 10), ("boot", a.n_boot, 30)):
    for v in range(base, base + n):
        print(variant, v, yardstick.phi_variant(a.dataset, a.d_sub, a.model, a.seed, variant, v, a.n_inst), flush=True)
