"""Loading of the pinned (model x item) binary score matrices."""
import os
import joblib
import numpy as np

DATA = os.environ.get("BP_DATA", "/hutian/data/raw")
OPENLLM = ["ifeval", "openllm_math", "mmlu_pro", "arc_challenge", "bbh", "gpqa", "musr"]
HELM = ["commonsense", "gsm", "legalbench", "math", "med_qa", "mmlu"]
ALL = OPENLLM + HELM


def load(name):
    """Return (X, models): X float32 {0,1} array (n_models, n_items); models list of names or None.
    Models whose full-benchmark accuracy is ~0 are dropped (all-zero rows carry no ranking information
    and are dropped the same way in the source repository's loader)."""
    X = joblib.load(os.path.join(DATA, f"{name}.jbl")).astype(np.float32)
    models = None
    p = os.path.join(DATA, f"{name}_models.jbl")
    if os.path.exists(p):
        models = list(joblib.load(p))
        assert len(models) == X.shape[0], (name, len(models), X.shape)
    keep = X.mean(1) > 1e-8
    X = X[keep]
    if models is not None:
        models = [m for m, k in zip(models, keep) if k]
    return X, models
