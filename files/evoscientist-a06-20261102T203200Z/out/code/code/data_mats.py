"""Build K x N correctness matrices from cached raw LLM outputs."""
import os, json, re, glob
import numpy as np, pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = BASE + "/data/mmlu-pro/data"
LET = "ABCDEFGHIJ"


def _test():
    return pd.read_parquet(f"{DATA}/test-00000-of-00001.parquet")


def parse(txt):
    m = re.match(r"\s*\(?\**([A-J])\b", txt)
    return m.group(1) if m else None


def api_matrix(model="claude-opus-4-5"):
    meta = json.load(open(f"{BASE}/cache/api_{model}_meta.json"))
    pool = np.array(meta["pool"]); cfgs = meta["configs"]
    test = _test()
    gold = np.array([test.iloc[int(p)]["answer_index"] for p in pool])
    cat = np.array([test.iloc[int(p)]["category"] for p in pool])
    K, N = len(cfgs), len(pool)
    S = np.full((K, N), np.nan); unparsed = np.zeros((K, N))
    for line in open(f"{BASE}/cache/api_{model}.jsonl"):
        d = json.loads(line)
        a = parse(d["r"])
        S[d["c"], d["q"]] = float(a is not None and LET.index(a) == gold[d["q"]])
        unparsed[d["c"], d["q"]] = a is None
    return S, cfgs, dict(cat=cat, gold=gold, pool=pool, unparsed=unparsed)


def local_matrix(model="Qwen2.5-0.5B-Instruct"):
    files = sorted(glob.glob(f"{BASE}/cache/local_{model}_s*.npz"))
    parts = [np.load(f) for f in files]
    cfgs = json.loads(str(parts[0]["cfgs"]))
    N = sum(p["correct"].shape[1] for p in parts)
    K = parts[0]["correct"].shape[0]
    S = np.zeros((K, N)); LP = np.zeros((K, N, 10), np.float32)
    for p in parts:
        S[:, p["qpos"]] = p["correct"]; LP[:, p["qpos"]] = p["logp"]
    test = _test()
    pool = np.random.RandomState(0).permutation(12032)[:N]
    cat = np.array([test.iloc[int(q)]["category"] for q in pool])
    return S, cfgs, dict(cat=cat, logp=LP, pool=pool)
