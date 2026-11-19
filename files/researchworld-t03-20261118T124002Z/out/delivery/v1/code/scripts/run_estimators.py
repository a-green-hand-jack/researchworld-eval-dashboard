import sys, argparse; sys.path.insert(0, __file__.rsplit("/scripts", 1)[0])
from shapaudit import runs
ap = argparse.ArgumentParser()
ap.add_argument("--cell"); ap.add_argument("--R", type=int, default=20); ap.add_argument("--tag", default="R20")
ap.add_argument("--inst", default=None, help="comma-separated instance numbers"); ap.add_argument("--arms", default=",".join(runs.ARMS))
ap.add_argument("--mults", default=",".join(map(str, runs.MULTS)))
a = ap.parse_args()
runs.run_cell(a.cell, R=a.R, inst=None if a.inst is None else [int(x) for x in a.inst.split(",")], arms=a.arms.split(","),
              mults=[float(x) for x in a.mults.split(",")], tag=a.tag, extra_budgets={"perm500": 500})
