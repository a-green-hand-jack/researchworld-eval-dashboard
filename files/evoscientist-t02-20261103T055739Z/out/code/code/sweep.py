"""Resumable parallel sweep runner. Usage: python sweep.py <name> <grid.json-producing-module-function> [workers]
Each finished run is appended as one JSON line to results/<name>.jsonl; runs whose key already exists are skipped."""
import sys, json, os, time, hashlib
from multiprocessing import Pool
import grok

ROOT = os.path.dirname(os.path.abspath(__file__))


def key(cfg):
    return hashlib.md5(json.dumps(cfg, sort_keys=True).encode()).hexdigest()


def _w(cfg):
    r = grok.run(cfg)
    r["key"] = key(cfg)
    return r


def run_grid(name, cfgs, workers=8):
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    path = os.path.join(ROOT, "results", name + ".jsonl")
    done = set()
    if os.path.exists(path):
        for l in open(path):
            try:
                done.add(json.loads(l)["key"])
            except Exception:
                pass
    todo = [c for c in cfgs if key(c) not in done]
    # longest first (large d first) for load balancing
    todo.sort(key=lambda c: -c.get("d", 0) * c.get("steps", 1))
    print(f"[{name}] {len(cfgs)} runs, {len(todo)} to do", flush=True)
    t0 = time.time()
    with Pool(workers, maxtasksperchild=1) as pool, open(path, "a") as f:
        for i, r in enumerate(pool.imap_unordered(_w, todo)):
            f.write(json.dumps(r) + "\n"); f.flush()
            c = r["cfg"]
            print(f"[{name}] {i+1}/{len(todo)} d={c['d']} seed={c['seed']} tf={r['t_fit']} tg={r['t_gen']} "
                  f"va={r['final_val_acc']:.3f} wall={r['wall']:.0f}s elapsed={time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    import importlib
    name = sys.argv[1]
    mod = importlib.import_module("grids")
    run_grid(name, getattr(mod, name)(), int(sys.argv[2]) if len(sys.argv) > 2 else 8)
