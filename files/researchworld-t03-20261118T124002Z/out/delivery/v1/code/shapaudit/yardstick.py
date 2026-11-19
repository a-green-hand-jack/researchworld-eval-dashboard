"""E4: the yardstick. Exact phi* of the same instances (a) under background resamples, (b) after retraining the model
(seed-only, and training-set bootstrap), saved under WORK/yard/<cell>/<variant>.npz (phi_star, pred, auc, acc)."""
import os
import numpy as np
from . import cells
from .estimators import exact_from_table


def phi_variant(name, d_sub, model, seed, variant, vid, n_inst=30, m=cells.M_BG, out="prob", work=cells.WORK):
    """variant: 'bg' (background resample vid, model seed `seed`), 'seed' (retrain with model seed vid), 'boot' (bootstrap retrain vid)."""
    cid = cells.cell_id(name, d_sub, model, seed, out)
    f = os.path.join(work, "yard", cid, f"{variant}{vid}.npz")
    if os.path.exists(f): return f
    kw = dict(bg_seed=vid) if variant == "bg" else {}
    ms = vid if variant in ("seed", "boot") else seed
    ds, enc, mod, bg_idx, inst_idx, info = cells.setup(name, d_sub, model, ms, m, cells.N_INST, train_mode="bootstrap" if variant == "boot" else "plain", out=out, **kw)
    ca = enc.col_attr(); Zb = enc(ds.X[bg_idx])
    phis, pred = [], []
    for i in inst_idx[:n_inst]:
        zx = enc(ds.X[i])[0]
        tab = mod.value_table(zx, Zb, ca, ds.d)
        phis.append(exact_from_table(tab, ds.d)); pred.append(float(tab[-1]))
    os.makedirs(os.path.dirname(f), exist_ok=True)
    np.savez(f, phi_star=np.array(phis), pred=np.array(pred), auc=info["auc"], acc=info["acc"], inst_idx=inst_idx[:n_inst])
    return f
