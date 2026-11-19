"""Sweep definitions and a skip-if-done runner.

python sweep.py run NAME SHARD NSHARDS [--procs 2]   # run shard SHARD of NSHARDS of sweep NAME
python sweep.py count NAME
Outputs: runs/<NAME>/<arch>_<op>_p<p>_f<frac>_wd<wd>_lr<lr>_w<width>_s<seed>.json
"""
import itertools, os, subprocess, sys
from multiprocessing.pool import ThreadPool

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = range(5)


def cfg(arch="tf", op="add", p=53, frac=0.4, wd=1.0, lr=1e-3, width=64, seed=0, max_steps=30000, init_mult=1.0, split_seed=-1, lr_ref=0, extra=500):
    return dict(arch=arch, op=op, p=p, frac=frac, wd=wd, lr=lr, width=width, seed=seed, max_steps=max_steps, init_mult=init_mult, split_seed=split_seed, lr_ref=lr_ref, extra=extra)


def sweeps():
    S = {}
    S["main"] = [cfg(width=w, seed=s) for w in (8, 16, 32, 64, 128, 256) for s in SEEDS]
    S["frac"] = [cfg(frac=f, width=w, seed=s) for f in (0.3, 0.5) for w in (16, 64, 256) for s in SEEDS]
    # Amendment 2 grid: wd in {0.5,2} (wd=1 from `main`) at two widths; wd=0.5 gets a 2x step budget
    S["wd"] = [cfg(wd=wd, width=w, seed=s, max_steps=60000 if wd < 1 else 30000) for wd in (0.5, 2.0) for w in (64, 128) for s in SEEDS]
    # scope (A3): f in {0.25, 0.5} (f=0.4 from `main`) at widths 32, 128. (runs/frac/ also holds two earlier f=0.3 width-16 runs)
    S["frac"] = [cfg(frac=f, width=w, seed=s) for f in (0.25, 0.5) for w in (32, 128) for s in SEEDS]
    S["mlp"] = [cfg(arch="mlp", width=w, seed=s) for w in (8, 16, 32, 64, 128, 256) for s in SEEDS]
    S["mul"] = [cfg(op="mul", width=w, seed=s) for w in (64, 128) for s in range(3)]
    # mechanism / scope / noise-source sweeps (plan A2, A3); alpha=1 and wd=1 cells are the `main` runs
    S["alpha"] = [cfg(init_mult=a, width=w, seed=s) for a in (0.5, 2.0) for w in (32, 128) for s in SEEDS]
    S["wd0"] = [cfg(wd=0.0, width=64, seed=s) for s in range(3)]
    S["lrscale"] = [cfg(lr_ref=64, width=w, seed=s) for w in (32, 128) for s in range(5)]  # seeds 0-2 first; 3-4 added later
    S["long"] = [cfg(width=w, seed=s, max_steps=100000) for w in (16, 32) for s in range(3)]  # T_max check for the narrow widths
    # threshold-1.0 sensitivity: the `main` runs of w>=64 that reached val 0.99 (a run is deterministic, so this reproduces it) continued 5000 steps past t_gen
    S["thr1"] = [cfg(width=w, seed=s, extra=5000) for w, s in ((64, 0), (64, 1), (64, 2), (64, 3), (128, 0), (128, 1), (128, 2), (128, 3), (128, 4), (256, 0), (256, 2), (256, 3), (256, 4))]
    # width-scaled lr over the full width range (lr*sqrt(64/width)); with `lrscale` (widths 32,128) forms the grid for the A1 slope under that parametrisation
    S["lrscale2"] = [cfg(lr_ref=64, width=w, seed=s) for w in (16, 64, 256) for s in range(3)]
    S["splitfix"] = [cfg(split_seed=0, width=w, seed=s) for w in (32, 64, 128) for s in SEEDS]
    return S


def path(name, c):
    extra = (f"_a{c['init_mult']}" if c["init_mult"] != 1.0 else "") + (f"_split{c['split_seed']}" if c["split_seed"] >= 0 else "") + (f"_lrref{c['lr_ref']}" if c["lr_ref"] else "")
    return os.path.join(HERE, "runs", name, f"{c['arch']}_{c['op']}_p{c['p']}_f{c['frac']}_wd{c['wd']}_lr{c['lr']}_w{c['width']}{extra}_s{c['seed']}.json")


def run_one(item):
    name, c = item
    out = path(name, c)
    if os.path.exists(out):
        return
    cmd = [sys.executable, os.path.join(HERE, "grok.py"), "--out", out, "--log_every", "250"] + sum(([f"--{k}", str(v)] for k, v in c.items()), [])
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    mode, name = sys.argv[1], sys.argv[2]
    items = [(name, c) for c in sweeps()[name]]
    if mode == "count":
        print(len(items)); sys.exit()
    shard, n = int(sys.argv[3]), int(sys.argv[4])
    procs = int(sys.argv[sys.argv.index("--procs") + 1]) if "--procs" in sys.argv else 2
    todo = items[shard::n]
    with ThreadPool(procs) as pool:
        list(pool.imap_unordered(run_one, todo))
