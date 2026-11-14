import os
for _v in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[_v]="1"
import sys, hashlib, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import multiprocessing as mp
import pandas as pd
from run_experiments import EXPS, RES
from gate_lib import *


def work(args):
    sid, sc = args
    seed = int(hashlib.md5(f"{sc['exp']}-{sid}".encode()).hexdigest()[:8], 16)
    sc = dict(sc, seed=seed)
    sc["estimators"] = [e for e in sc["pred_for"]]
    ctx = Context(sc)
    rows = []
    for nm in sc["pred_for"]:
        r = predict_ols2(ctx, nm, R=300, R2=300, seed=seed)
        r.update(sid=sid, est=nm)
        rows.append(r)
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("exps", nargs="+"); ap.add_argument("--procs", type=int, default=20)
    a = ap.parse_args()
    for e in a.exps:
        S = EXPS[e]()
        jobs = list(enumerate(S))
        jobs.sort(key=lambda j: -(j[1]["graph"].get("n", 12000) * (1 + j[1]["graph"].get("d", 100) / 20)))
        t0 = time.time(); rows = []
        with mp.Pool(a.procs, maxtasksperchild=10) as pool:
            for i, r in enumerate(pool.imap_unordered(work, jobs)):
                rows += r
                if (i + 1) % 25 == 0: print(e, i + 1, len(jobs), f"{time.time()-t0:.0f}s", flush=True)
        pd.DataFrame(rows).to_csv(os.path.join(RES, f"{e}_pred2.csv"), index=False)
        print(e, "done", f"{time.time()-t0:.0f}s", flush=True)
