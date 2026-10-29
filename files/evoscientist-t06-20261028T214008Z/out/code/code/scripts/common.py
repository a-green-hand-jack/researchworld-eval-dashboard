import os
import sys
import time
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.chdir(ROOT)  # data paths are relative to the workspace root

RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "paper", "figures")
os.makedirs(RES, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

MAIN = ["arena55k", "arena140k", "mt_human", "mt_gpt4"]
NBA = [f"nba{y}" for y in range(1990, 2016)]
NPROC = int(os.environ.get("LB_NPROC", "8"))


class Timer:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.t = time.time()
        return self

    def __exit__(self, *a):
        print(f"[{self.name}] {time.time() - self.t:.1f}s", flush=True)


def dump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=float)
