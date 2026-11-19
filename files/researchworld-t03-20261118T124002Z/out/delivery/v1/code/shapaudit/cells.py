"""A *cell* = (dataset, d-subset, model class, model seed). Building a cell trains the model, fixes the background
set D and the explained instances, and writes the exact value table v(S) of every instance (the exact enumeration =
target phi*) to the work directory."""
import json, os, time
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from . import data, models

WORK = os.environ.get("SHAPAUDIT_WORK", "/hutian/work")
M_BG = 30          # background size m
N_INST = 100       # explained instances per cell
SPLIT_SEED = 0     # train/test split, background rows and instance indices are fixed across model seeds


def load(name):
    if name == "german": return data.german()
    if name == "arrhythmia": return data.arrhythmia()
    if name.startswith("ACS"):
        task, state, year = name.split(":") if ":" in name else (name, "AL", "2018")
        return data.acs(task, state, year)
    raise ValueError(name)


def subset(ds, d_sub, seed=SPLIT_SEED):
    """feature subsetting to control d: a fixed random subset of attributes (same for every model/seed)."""
    if d_sub is None or d_sub >= ds.d:
        return ds
    rng = np.random.default_rng(1000 + seed)
    keep = np.sort(rng.choice(ds.d, d_sub, replace=False))
    out = data.Dataset(ds.name + f"_d{d_sub}", ds.X[:, keep], ds.y, ds.is_cat[keep], [ds.names[j] for j in keep])
    return out


def cell_id(name, d_sub, model, seed, out="prob"):
    return f"{name.replace(':', '-')}_d{d_sub or 'full'}_{model}{'_logit' if out == 'logit' else ''}_s{seed}"


def setup(name, d_sub, model, seed, m=M_BG, n_inst=N_INST, train_mode="plain", split_seed=SPLIT_SEED, out="prob", bg_seed=None):
    ds = subset(load(name), d_sub)
    idx = np.arange(len(ds.y))
    tr, te = train_test_split(idx, test_size=0.3 if ds.X.shape[0] < 5000 else 0.2, random_state=split_seed, stratify=ds.y)
    onehot = model in ("lr", "mlp")
    enc = data.Encoder(onehot=onehot).fit(ds, ds.X[tr])
    rng = np.random.default_rng(split_seed + 7)
    bg_idx = rng.choice(tr, m, replace=False)
    if bg_seed is not None:                      # E4: an independent background draw (instances stay fixed)
        bg_idx = np.random.default_rng(10_000 + bg_seed).choice(tr, m, replace=False)
    inst_idx = rng.choice(te, min(n_inst, len(te)), replace=False)
    fit_tr = tr
    if train_mode == "bootstrap":
        fit_tr = np.random.default_rng(seed + 99).choice(tr, len(tr), replace=True)
    mod = models.MODELS[model](seed=seed).fit(enc(ds.X[fit_tr]), ds.y[fit_tr])
    p_te = mod.predict(enc(ds.X[te]))
    if out == "logit":
        mod.out = "logit"
    info = dict(acc=float(((p_te > .5) == ds.y[te]).mean()), auc=float(roc_auc_score(ds.y[te], p_te)),
                base_rate=float(ds.y[te].mean()), n_train=int(len(tr)), n_test=int(len(te)), d=int(ds.d), p=int(enc.p))
    return ds, enc, mod, bg_idx, inst_idx, info


def varying(ds, x, bg_idx):
    """attributes on which x differs from at least one background row (the players shap would keep)."""
    return np.where((ds.X[bg_idx] != x[None, :]).any(0))[0]


def build(name, d_sub, model, seed, m=M_BG, n_inst=N_INST, out=None, verbose=True, output="prob"):
    from .estimators import exact_from_table
    cid = cell_id(name, d_sub, model, seed, output)
    out = out or os.path.join(WORK, "cells", cid)
    os.makedirs(out, exist_ok=True)
    ds, enc, mod, bg_idx, inst_idx, info = setup(name, d_sub, model, seed, m, n_inst, out=output)
    mf = os.path.join(out, "meta.json")
    if os.path.exists(mf) and json.load(open(mf))["n_inst"] != len(inst_idx):   # the instance draw depends on n_inst: cached tables would belong to other instances
        raise RuntimeError(f"{cid}: cached tables were built with n_inst={json.load(open(mf))['n_inst']}; delete {out} to rebuild")
    ca = enc.col_attr()
    Zb = enc(ds.X[bg_idx])
    phis, times, pred = [], [], []
    check = {}
    for t, i in enumerate(inst_idx):
        f = os.path.join(out, f"tab_{t:03d}.npy")
        zx = enc(ds.X[i])[0]
        if os.path.exists(f):
            tab = np.load(f)
        else:
            t0 = time.time(); tab = mod.value_table(zx, Zb, ca, ds.d); times.append(time.time() - t0)
            np.save(f, tab)
        phi = exact_from_table(tab, ds.d)
        phis.append(phi); pred.append(float(mod.predict(zx[None])[0]))
        assert abs(tab[-1] - pred[-1]) < 2e-4, (tab[-1], pred[-1])
        if model == "gbdt" and t < 3:           # E0: table-enumeration vs interventional TreeSHAP (player = column = attribute)
            import shap
            te = shap.TreeExplainer(mod.m, data=Zb, feature_perturbation="interventional", model_output="probability" if output == "prob" else "raw")
            ph_ts = te.shap_values(zx[None], check_additivity=False)
            ph_ts = ph_ts[1] if isinstance(ph_ts, list) else ph_ts
            ph_ts = np.asarray(ph_ts).reshape(-1, ds.d)[0] if np.asarray(ph_ts).ndim == 3 else np.asarray(ph_ts)[0]
            check[f"treeshap_maxabs_{t}"] = float(np.abs(ph_ts - phi).max())
        if verbose and t % 10 == 0:
            print(cid, t, "table s", round(times[-1], 1) if times else "cached", flush=True)
    np.savez(os.path.join(out, "meta.npz"), inst_idx=inst_idx, bg_idx=bg_idx, phi_star=np.array(phis), pred=np.array(pred),
             v0=np.array([float(np.load(os.path.join(out, f"tab_{t:03d}.npy"), mmap_mode="r")[0]) for t in range(len(inst_idx))]))
    meta = dict(cell=cid, output=output, dataset=name, d_sub=d_sub, model=model, seed=seed, m=m, n_inst=len(inst_idx), names=ds.names,
                table_seconds_mean=float(np.mean(times)) if times else None, **info, **check)
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=1)
    return meta


class LiveVF:
    """Value function of one instance evaluated live on the model (no table): v(S) = mean_k f(x_S, b_k,~S). For d above the enumeration range."""
    def __init__(self, mod, zx, Zb, col_attr, d, chunk_rows=200_000):
        self.mod, self.zx, self.Zb, self.ca, self.d, self.chunk = mod, zx, Zb, col_attr, d, chunk_rows
        self.v0 = float(self.value_masks(np.zeros((1, d), np.float32))[0]); self.vN = float(self.value_masks(np.ones((1, d), np.float32))[0])
    def value_masks(self, full):
        return self.mod.value_masks(full, self.zx, self.Zb, self.ca, chunk_rows=self.chunk)


def build_live(name, d_sub, model, seed, m=M_BG, n_inst=N_INST, out=None, verbose=True, output="logit"):
    """d above the table range (GBDT on the raw margin): the exact target is interventional TreeSHAP of the same (f, x, D)."""
    import shap
    assert model == "gbdt"
    cid = cell_id(name, d_sub, model, seed, output)
    out = out or os.path.join(WORK, "cells", cid)
    os.makedirs(out, exist_ok=True)
    ds, enc, mod, bg_idx, inst_idx, info = setup(name, d_sub, model, seed, m, n_inst, out=output)
    ca = enc.col_attr(); Zb = enc(ds.X[bg_idx])
    te = shap.TreeExplainer(mod.m, data=Zb, feature_perturbation="interventional", model_output="raw")
    phis, v0s, pred, times, adds = [], [], [], [], []
    for t, i in enumerate(inst_idx):
        zx = enc(ds.X[i])[0]
        t0 = time.time(); ph = np.asarray(te.shap_values(zx[None], check_additivity=False)).reshape(-1, ds.d)[0]; times.append(time.time() - t0)
        vf = LiveVF(mod, zx, Zb, ca, ds.d)
        adds.append(float(abs(ph.sum() - (vf.vN - vf.v0))))
        phis.append(ph); v0s.append(vf.v0); pred.append(vf.vN)
        if verbose and t % 10 == 0: print(cid, t, "treeshap s", round(times[-1], 1), "additivity err", round(adds[-1], 6), flush=True)
    np.savez(os.path.join(out, "meta.npz"), inst_idx=inst_idx, bg_idx=bg_idx, phi_star=np.array(phis), pred=np.array(pred), v0=np.array(v0s))
    meta = dict(cell=cid, output=output, live=True, dataset=name, d_sub=d_sub, model=model, seed=seed, m=m, n_inst=len(inst_idx), names=ds.names,
                treeshap_seconds_mean=float(np.mean(times)), additivity_err_max=float(np.max(adds)), **info)
    json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=1)
    return meta
