import sys, argparse; sys.path.insert(0, __file__.rsplit("/scripts", 1)[0])
from shapaudit import runs
ap = argparse.ArgumentParser()
ap.add_argument("--cell"); ap.add_argument("--R", type=int, default=20); ap.add_argument("--tag", default="certs")
ap.add_argument("--inst", default=None)
a = ap.parse_args()
runs.run_certs(a.cell, R=a.R, tag=a.tag, inst=None if a.inst is None else [int(x) for x in a.inst.split(",")])
