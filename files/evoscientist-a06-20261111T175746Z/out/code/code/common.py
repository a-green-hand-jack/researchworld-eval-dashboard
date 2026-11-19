import glob, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))


def load_matrix(tag, nmax=None):
    """Returns Y (K x N float32 correctness), meta dict. Uses all configs for which cfg*.npy exists."""
    d = f"results/raw/{tag}"
    meta = json.load(open(f"{d}/meta.json"))
    ans = np.array(meta["answer_index"])
    ks, Ys = [], []
    for k in range(meta["K"]):
        f = f"{d}/cfg{k}.npy"
        if os.path.exists(f):
            sc = np.load(f)
            Ys.append((sc.argmax(1) == ans).astype(np.float32)); ks.append(k)
    Y = np.stack(Ys)
    meta["cfg_ids"] = ks
    if nmax:
        Y = Y[:, :nmax]
        meta["category"] = meta["category"][:nmax]
    return Y, meta


def pmap(fn, jobs, nproc=3):
    import multiprocessing as mp
    if nproc <= 1:
        return [fn(j) for j in jobs]
    with mp.get_context("fork").Pool(nproc) as p:
        return p.map(fn, jobs, chunksize=1)


def to_py(o):
    if isinstance(o, dict):
        return {k: to_py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_py(v) for v in o]
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    return o
