"""Resumable parallel sweep runner.  usage: python sweep.py <grid_module_or_json> <outdir> [nproc]
Each run is saved to <outdir>/<name>.json; existing files are skipped."""
import sys, os, json, hashlib, multiprocessing as mp
sys.path.insert(0, os.path.dirname(__file__))


def name_of(cfg):
    keys = ["arch", "p", "frac", "width", "layers", "lr", "wd", "seed", "op", "bs", "heads", "mlp_mult", "steps", "split_seed", "rescale"]
    return "_".join(f"{k}{cfg[k]}" for k in keys if k in cfg)


def _work(args):
    cfg, outdir = args
    import grok
    fn = os.path.join(outdir, name_of(cfg) + ".json")
    if os.path.exists(fn):
        return fn
    out = grok.run(cfg)
    tmp = fn + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f)
    os.replace(tmp, fn)
    return fn


def _work_ens(args):
    cfgs, outdir = args  # same cfg except seed
    import grok
    outs = grok.run_ens(cfgs[0], [c["seed"] for c in cfgs])
    for c, out in zip(cfgs, outs):
        fn = os.path.join(outdir, name_of(c) + ".json")
        with open(fn + ".tmp", "w") as f:
            json.dump(out, f)
        os.replace(fn + ".tmp", fn)
    return fn


def run_grid_ens(cfgs, outdir, nproc=4):
    """Like run_grid but groups configs that differ only in seed and trains them as a seed-ensemble (tf only)."""
    os.makedirs(outdir, exist_ok=True)
    groups = {}
    for c in cfgs:
        if os.path.exists(os.path.join(outdir, name_of(c) + ".json")):
            continue
        k = json.dumps({a: b for a, b in c.items() if a != "seed"}, sort_keys=True)
        groups.setdefault(k, []).append(c)
    todo = [(g, outdir) for g in groups.values()]
    todo.sort(key=lambda a: -(a[0][0]["steps"] * a[0][0]["width"] * a[0][0]["p"] ** 2 * a[0][0]["frac"] * len(a[0])))
    print(f"{len(todo)} ensemble jobs", flush=True)
    with mp.Pool(nproc, maxtasksperchild=1) as pool:
        for i, fn in enumerate(pool.imap_unordered(_work_ens, todo)):
            print(i, fn, flush=True)


def run_grid(cfgs, outdir, nproc=4):
    os.makedirs(outdir, exist_ok=True)
    todo = [(c, outdir) for c in cfgs if not os.path.exists(os.path.join(outdir, name_of(c) + ".json"))]
    # longest jobs first for load balancing
    todo.sort(key=lambda a: -(a[0]["steps"] * a[0]["width"] * a[0]["p"] ** 2 * a[0]["frac"]))
    print(f"{len(todo)} runs to do ({len(cfgs)-len(todo)} cached)", flush=True)
    with mp.Pool(nproc, maxtasksperchild=1) as pool:
        for i, fn in enumerate(pool.imap_unordered(_work, todo)):
            if i % 10 == 0:
                print(i, fn, flush=True)


def load_all(outdir):
    res = []
    for fn in sorted(os.listdir(outdir)):
        if fn.endswith(".json"):
            with open(os.path.join(outdir, fn)) as f:
                res.append(json.load(f))
    return res
