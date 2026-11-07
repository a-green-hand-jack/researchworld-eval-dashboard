"""Generic sweep runner: python sweep.py <name> ; configs come from experiments.py:<name>().
Appends one JSON line per finished run to results/<name>.jsonl (resumable, skips finished keys)."""
import sys, json, os, itertools
import multiprocessing as mp
os.environ.setdefault("OMP_NUM_THREADS", "1")

def key(c): return json.dumps(c, sort_keys=True)

def work(cfg):
    import grok
    r = grok.run(cfg)
    r["key"] = key(cfg)
    r["curve"] = [[round(x, 5) if isinstance(x, float) else x for x in row] for row in r["curve"]]
    return r

if __name__ == "__main__":
    import experiments
    name = sys.argv[1]; nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    cfgs = getattr(experiments, name)()
    path = f"/work/results/{name}.jsonl"
    done = set()
    if os.path.exists(path):
        for l in open(path): done.add(json.loads(l)["key"])
    todo = [c for c in cfgs if key(c) not in done]
    print(f"{name}: {len(cfgs)} configs, {len(todo)} to run", flush=True)
    # longest jobs first for balance
    todo.sort(key=lambda c: -(c.get("width", 0)))
    with mp.Pool(nproc) as pool, open(path, "a") as f:
        for i, r in enumerate(pool.imap_unordered(work, todo)):
            f.write(json.dumps(r) + "\n"); f.flush()
            c = r["cfg"]
            print(f"[{i+1}/{len(todo)}] {c['arch']} w={c['width']} lr={c['lr']} wd={c['wd']} s={c['seed']} "
                  f"fit={r['t_fit']} gen={r['t_gen']} va={r['final_va_acc']:.3f} {r['secs']:.0f}s", flush=True)
