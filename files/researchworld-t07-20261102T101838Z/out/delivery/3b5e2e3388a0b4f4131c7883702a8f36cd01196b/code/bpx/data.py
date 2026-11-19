"""Loading of the pinned per-item score matrices (benchmark-prediction repo, commit 55faff49...)."""
import hashlib, os
import joblib, numpy as np

DATA_DIR = os.environ.get("BP_DATA", "/hutian/data/raw")
OPENLLM = ["arc_challenge", "bbh", "gpqa", "ifeval", "mmlu_pro", "musr", "openllm_math"]
HELM = ["commonsense", "gsm", "legalbench", "math", "med_qa", "mmlu"]
BENCHMARKS = OPENLLM + HELM


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load(name, dedup=True):
    """Return (S, names, info). S: (M, N) uint8 matrix of 0/1; duplicate model rows
    (identical response vectors) are collapsed to the first one when dedup=True."""
    S = np.asarray(joblib.load(os.path.join(DATA_DIR, name + ".jbl"))).astype(np.uint8)
    if name in OPENLLM:
        names = list(joblib.load(os.path.join(DATA_DIR, name + "_models.jbl")))
    else:
        names = open(os.path.join(DATA_DIR, "helm_model_list.txt")).read().split("\n")
    names = [n for n in names if n != ""]
    if name in OPENLLM:
        assert len(names) == S.shape[0], (name, len(names), S.shape)     # per-benchmark model list ships with the matrix
        verified = True
    else:
        # HELM files have no per-benchmark model list: only the global helm_model_list.txt; row order is ASSUMED to follow it
        # when the counts agree (unverifiable); otherwise names are anonymous.
        verified = False
        if len(names) != S.shape[0]:
            names = [f"helm_row{i}" for i in range(S.shape[0])]
    info = {"M_raw": S.shape[0], "N": S.shape[1], "names_verified": verified}
    if dedup:
        seen, keep = set(), []
        for i, r in enumerate(S):
            k = r.tobytes()
            if k not in seen:
                seen.add(k); keep.append(i)
        S = S[keep]; names = [names[i] for i in keep]
    info["M"] = S.shape[0]
    return S, names, info


def org_of(model_name):
    return model_name.split("/")[0] if "/" in model_name else model_name.split("_")[0]
