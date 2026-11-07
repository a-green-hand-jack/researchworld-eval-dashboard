"""T1: replay of searches on the cached real LLM outcome matrix (MMLU-Pro pool x 24 base prompt configs + 276 pairwise
logit-average ensembles). usage: t1.py MODEL SHARD NSHARDS [--reps R] [--out DIR]"""
import sys, os, glob, time, argparse, itertools, zlib, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import configs as C, lib, methods
SEED = 20261103

def load_matrix(model, n_pool, chunk, root="/hutian/repo/results/logits"):
    """Returns logp [24, N_avail, 10] for the largest prefix of chunks present for all 24 base configs, pool positional indices."""
    d = f"{root}/{model}"; ch = 0
    while ch * chunk < n_pool and all(os.path.exists(f"{d}/{k:02d}__c{ch}.npy") for k in range(len(C.BASE))): ch += 1
    L = np.stack([np.concatenate([np.load(f"{d}/{k:02d}__c{c}.npy") for c in range(ch)]) for k in range(len(C.BASE))]).astype(np.float32)
    pool = C.pool_indices(n_pool)[:L.shape[1]]
    return L, pool

def correctness(L, ans):
    """L: [24,N,10] option log-probs. Returns Y [300,N] uint8 (24 base then 276 pair ensembles), names"""
    Yb = (L.argmax(2) == ans[None]).astype(np.uint8); rows = [Yb]; names = list(C.BASE)
    for a, b in itertools.combinations(range(L.shape[0]), 2):
        rows.append(((L[a] + L[b]).argmax(1) == ans)[None].astype(np.uint8)); names.append(f"ens({C.BASE[a]}+{C.BASE[b]})")
    return np.concatenate(rows), names

G = 10   # pool blocks (delete-a-block): replicate r draws D and the fresh set from the pool without block r % G

def cells(reps=500):
    out = []
    def add(proc, n, K, m3=False): out.append(dict(proc=proc, n=n, K=K, m3_B=100 if m3 else 0, reps=200 if m3 else reps, cell_id=f"proc={proc}|n={n}|K={K}" + ("|m3" if m3 else "")))
    for n in (50, 100, 200, 300, 500):
        for K in (2, 5, 10, 24, 50, 100, 300): add("exhaustive", n, K)
    for n in (100, 200, 500):
        for K in (24, 100, 300): add("halving", n, K)
    for n in (50, 100, 200, 500): add("greedy", n, 24)
    for n in (100, 500):
        for K in (24, 300): add("exhaustive", n, K, m3=True)
    return out

def run_cell(c, Y, subj, rng_seed, names, nreps=None):
    N = Y.shape[1]; n, K, proc = c["n"], c["K"], c["proc"]; nrep = nreps or c["reps"]
    runs, meths, sub = [], [], []
    for rep in range(nrep):
        rng = np.random.default_rng([rng_seed, zlib.crc32(c["cell_id"].encode()), rep])
        if K == 24:
            sel = np.arange(24); levels = lib.LEVELS[24]
        else:
            sel = np.concatenate([[0], rng.choice(np.arange(1, Y.shape[0]), K - 1, replace=False)]); levels = (K,)
        blk = rep % G; avail = np.flatnonzero(np.arange(N) % G != blk)
        D = rng.choice(avail, n, replace=False); F = np.setdiff1d(avail, D)
        Yd = Y[np.ix_(sel, D)]; th = Y[np.ix_(sel, F)].mean(1)
        run, rows = methods.run_methods(Yd, th, proc, levels, rng, opts=dict(m3_B=c["m3_B"]))
        meta = dict(tier="T1", cell_id=c["cell_id"], rep=rep, seed=rng_seed, n=n, K=K, tau=np.nan, rho=np.nan, base_acc=float(Y[0].mean()),
                    procedure=proc, leakage=0, subject="all", block=blk, n_fresh=len(F), theta_se=float(np.sqrt(th[run["chosen_config"]] * (1 - th[run["chosen_config"]]) / len(F))))
        runs.append({**meta, **run, "chosen_name": names[sel[run["chosen_config"]]]})
        for r in rows: meths.append({**{k: meta[k] for k in ("tier", "cell_id", "rep", "n", "K", "tau", "rho", "base_acc", "procedure")}, **r})
        if c["m3_B"] == 0 and proc == "exhaustive" and K in (24, 300):    # per-subject breakdown of the gap for the selected config
            ch = sel[run["chosen_config"]]
            for s in np.unique(subj):
                di, fi = D[subj[D] == s], F[subj[F] == s]
                if len(di) and len(fi): sub.append(dict(cell_id=c["cell_id"], rep=rep, subject=s, n_search_items=len(di), n_fresh_items=len(fi),
                                                       reported=float(Y[ch, di].mean()), fresh=float(Y[ch, fi].mean())))
    return runs, meths, sub

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("shard", type=int); ap.add_argument("nshards", type=int)
    ap.add_argument("--reps", type=int, default=None); ap.add_argument("--n_pool", type=int, default=2000); ap.add_argument("--chunk", type=int, default=250)
    ap.add_argument("--out", default="/hutian/repo/results/t1"); ap.add_argument("--cells", default=None)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    L, pool = load_matrix(a.model, a.n_pool, a.chunk); test = C.load_test()
    ans = test.answer_index.values[pool]; subj = test.category.values[pool]
    Y, names = correctness(L, ans); print(f"pool items available: {Y.shape[1]}; base acc range {Y[:24].mean(1).min():.3f}-{Y[:24].mean(1).max():.3f}", flush=True)
    tag = f"{a.model}.shard{a.shard}"; runs, meths, subs = [], [], []
    cs = [c for i, c in enumerate(cells()) if i % a.nshards == a.shard and (a.cells is None or a.cells in c["cell_id"])]
    for i, c in enumerate(cs):
        t = time.time(); r, m, s = run_cell(c, Y, subj, SEED, names, a.reps); runs += r; meths += m; subs += s
        print(f"HUTIAN_PROGRESS {i+1}/{len(cs)} {c['cell_id']} {time.time()-t:.0f}s", flush=True)
    pd.DataFrame(runs).to_parquet(f"{a.out}/{tag}.runs.parquet"); pd.DataFrame(meths).to_parquet(f"{a.out}/{tag}.methods.parquet"); pd.DataFrame(subs).to_parquet(f"{a.out}/{tag}.subjects.parquet")
