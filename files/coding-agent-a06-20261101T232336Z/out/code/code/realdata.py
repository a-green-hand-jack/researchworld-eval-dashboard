"""Load the cached Qwen log-probs and convert to a correctness matrix Y[item, config]."""
import glob, numpy as np, sys
sys.path.insert(0, "/work/code")
from common import *

def load_cache(cache_dir):
    df = load_test()
    lps, pos = [], []
    for f in sorted(glob.glob(f"{cache_dir}/chunk_*.npz")):
        z = np.load(f); lps.append(z["lp"]); pos.append(z["item_pos"])
    lp = np.concatenate(lps); pos = np.concatenate(pos)
    ans = df["answer_index"].values[pos]
    cat = df["category"].values[pos]
    return lp, pos, ans, cat

def load_Y(cache_dir, pool=None):
    lp, pos, ans, cat = load_cache(cache_dir)
    Y = (lp.argmax(-1) == ans[:, None]).astype(np.uint8)
    if pool is not None: Y = Y[:, pool]
    return Y

def load_meta(cache_dir):
    lp, pos, ans, cat = load_cache(cache_dir)
    return pos, ans, cat


def load_pool2(models=("m_qwen3_06b", "m_qwen25_05b", "m_qwen2_15b", "m_qwen3_17b"), main="/work/cache/q15", root="/work/cache", return_names=False):
    """Model x prompt pool: 4 prompt variants x 2 groups (zero-shot, 3-shot) per model; Qwen2.5-1.5B taken from the main grid.
    Returns Y[items, configs] on the items available for all models."""
    df = load_test()
    def read(dirn, cols=None):
        out = {}
        for f in sorted(glob.glob(f"{dirn}/chunk_*.npz")):
            z = np.load(f); lp = z["lp"]; ans = df["answer_index"].values[z["item_pos"]]
            y = (lp.argmax(-1) == ans[:, None]).astype(np.uint8)
            if cols is not None: y = y[:, cols]
            for ip, row in zip(z["item_perm"], y): out[int(ip)] = row
        return out
    d = {"qwen25_15b": read(main, [0, 1, 3, 4, 12, 13, 15, 16])}
    for m in models:
        if glob.glob(f"{root}/{m}/chunk_*.npz"): d[m] = read(f"{root}/{m}")
    common = sorted(set.intersection(*[set(v) for v in d.values()]))
    Y = np.concatenate([np.stack([d[m][i] for i in common]) for m in d], axis=1)
    names = [f"{m}:{j}" for m in d for j in range(8)]
    return (Y, names) if return_names else Y
