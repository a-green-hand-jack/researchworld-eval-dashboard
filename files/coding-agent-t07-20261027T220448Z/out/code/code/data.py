"""Data loading for the benchmark-prediction study (Open LLM Leaderboard v2 + HELM binary item-level matrices)."""
import os, joblib, numpy as np

RAW = os.environ.get("BP_RAW", "/work/data/raw")
OPENLLM = ["arc_challenge", "bbh", "gpqa", "ifeval", "mmlu_pro", "musr", "openllm_math"]
HELM = ["commonsense", "gsm", "legalbench", "math", "med_qa", "mmlu"]
ALL = OPENLLM + HELM


def load(name):
    """Returns (Y float32 [models x items] in {0,1}, org list or None)."""
    Y = np.asarray(joblib.load(os.path.join(RAW, name + ".jbl")))
    assert not np.isnan(Y.astype(float)).any()
    Y = Y.astype(np.float32)
    assert set(np.unique(Y)) <= {0.0, 1.0}
    orgs = None
    if name in OPENLLM:
        models = joblib.load(os.path.join(RAW, name + "_models.jbl"))
        assert len(models) == Y.shape[0]
        orgs = [m.split("/")[0] for m in models]
    return Y, orgs


if __name__ == "__main__":
    for n in ALL:
        Y, o = load(n)
        acc = Y.mean(1)
        # drop-in sanity: constant items / duplicated model rows
        dup = Y.shape[0] - len({r.tobytes() for r in Y})
        const = int(((Y.mean(0) == 0) | (Y.mean(0) == 1)).sum())
        print(f"{n:15s} models={Y.shape[0]:4d} items={Y.shape[1]:6d} acc mean={acc.mean():.3f} sd={acc.std():.3f} "
              f"min={acc.min():.3f} max={acc.max():.3f} constant_items={const} dup_rows={dup} orgs={len(set(o)) if o else None}")
