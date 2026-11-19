"""Train the base models (seed 0), draw explained instances and background; save to artifacts/ and log accuracy."""
import os, sys, json, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np, joblib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C, data, models

os.makedirs(C.ART, exist_ok=True)
perf = {}
for dn in C.DATASETS + [C.E5_DS]:
    D = data.load(dn, seed=C.SEED_DATA)
    rs = np.random.RandomState(C.SEED_INST)
    n = C.E5_N if dn == C.E5_DS else C.N_INST
    inst = rs.choice(len(D["yte"]), n, replace=False)
    bg = D["Xtr"][np.random.RandomState(C.SEED_BG).choice(len(D["ytr"]), C.M_BG, replace=False)]
    joblib.dump(dict(Xte=D["Xte"][inst], yte=D["yte"][inst], inst_idx=inst, bg=bg, names=D["names"], cat=D["cat"],
                     Xtr=D["Xtr"], ytr=D["ytr"]), f"{C.ART}/{dn}_data.joblib")
    for k in (C.MODELS if dn != C.E5_DS else C.E5_MODELS):
        t = time.time(); m = models.train(k, D, seed=0)
        s = m.score(D["Xte"], D["yte"]); s["train_s"] = time.time() - t
        s["pos_rate_test"] = float(D["yte"].mean()); s["n_train"] = int(len(D["ytr"])); s["d"] = int(D["X"].shape[1])
        perf[f"{dn}/{k}"] = s
        joblib.dump(m, f"{C.ART}/{dn}_{k}.joblib")
        print(dn, k, s, flush=True)
os.makedirs(C.RES, exist_ok=True)
json.dump(perf, open(f"{C.RES}/model_performance.json", "w"), indent=1)
