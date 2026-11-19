"""Generic parallel sweep driver. Usage: python sweep.py <experiment_name>
Experiments are defined in experiments.py as functions returning lists of cfg dicts.
Results append to results/<name>.jsonl; finished configs (by key) are skipped on restart."""
import sys, os, json, multiprocessing as mp, time
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
sys.path.insert(0, os.path.dirname(__file__))
import grok, experiments

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def key(cfg):
    return json.dumps(cfg, sort_keys=True)


def work(cfg):
    r = grok.run(cfg)
    r["key"] = key(cfg)
    return r


if __name__ == "__main__":
    name = sys.argv[1]
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 36
    os.makedirs(ROOT, exist_ok=True)
    out = os.path.join(ROOT, name + ".jsonl")
    cfgs = getattr(experiments, name)()
    done = set()
    if os.path.exists(out):
        for l in open(out):
            done.add(json.loads(l)["key"])
    todo = [c for c in cfgs if key(c) not in done]
    # longest jobs first (large width) for load balance
    todo.sort(key=lambda c: -(c.get("width", 0) * c.get("max_steps", 30000)))
    print(f"{name}: {len(cfgs)} cfgs, {len(todo)} to run", flush=True)
    t0 = time.time()
    with mp.Pool(nproc) as pool, open(out, "a") as f:
        for i, r in enumerate(pool.imap_unordered(work, todo)):
            f.write(json.dumps(r) + "\n"); f.flush()
            if i % 10 == 0:
                print(f"[{time.time()-t0:.0f}s] {i+1}/{len(todo)} last: w={r['cfg']['width']} "
                      f"tt={r['t_train']} tv={r['t_val']} {r['secs']:.0f}s", flush=True)
    print("done", time.time() - t0)
