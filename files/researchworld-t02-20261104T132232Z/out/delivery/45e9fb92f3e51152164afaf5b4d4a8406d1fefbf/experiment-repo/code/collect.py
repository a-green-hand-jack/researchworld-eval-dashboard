"""Collect per-run JSONs into tidy tables: python3 collect.py RUNDIR OUTPREFIX

Writes OUTPREFIX_runs.csv (one row per run) and OUTPREFIX_curves.csv (log-spaced curve points).
Threshold columns: t_fit99/t_gen99 etc. are the first logged step at which the accuracy reached the
threshold; empty = never reached within `steps_run` (right-censored at steps_run; `max_steps` is the budget).
"""
import glob, json, os, sys
import numpy as np
import pandas as pd


K_SUSTAIN = 3   # sustained crossing: first logged step from which the accuracy stays >= thr for K_SUSTAIN consecutive evaluations


def sustained(steps, acc, thr, k=K_SUSTAIN):
    acc = np.asarray(acc)
    for i in range(len(acc)):
        if acc[i] >= thr and (acc[i:i + k] >= thr).all() and i + k <= len(acc):
            return int(steps[i])
    return None


def main(rundir, prefix):
    rows, curves = [], []
    for f in sorted(glob.glob(os.path.join(rundir, "*.json"))):
        r = json.load(open(f)); c, s, l = r["config"], r["summary"], r["log"]
        rid = os.path.basename(f)[:-5]
        sus = {"t_fit99_s": sustained(l["step"], l["train_acc"], .99), "t_gen99_s": sustained(l["step"], l["val_acc"], .99),
               "t_gen50_s": sustained(l["step"], l["val_acc"], .5), "t_gen95_s": sustained(l["step"], l["val_acc"], .95)}
        rows.append({"run_id": rid, **{k: c[k] for k in ["task", "p", "model", "width", "depth", "lr", "wd", "init_scale",
                     "train_frac", "seed", "max_steps", "eval_every"]}, **s, **sus})
        steps = np.array(l["step"])
        keep = {0, len(steps) - 1}
        for tgt in np.unique(np.round(np.geomspace(1, max(steps.max(), 2), 60))):
            keep.add(int(np.abs(steps - tgt).argmin()))
        for i in sorted(keep):
            curves.append({"run_id": rid, **{k: l[k][i] for k in l}})
    df = pd.DataFrame(rows)
    df["n_train"] = (df.train_frac * df.p ** 2).round().astype(int)
    df["fit_censored"] = df.t_fit99.isna(); df["gen_censored"] = df.t_gen99.isna()
    df["delay99"] = df.t_gen99 - df.t_fit99
    df["delay99_s"] = df.t_gen99_s - df.t_fit99_s   # sustained-crossing delay (SPEC primary)
    df.to_csv(prefix + "_runs.csv", index=False)
    pd.DataFrame(curves).to_csv(prefix + "_curves.csv", index=False)
    print(len(df), "runs ->", prefix + "_runs.csv")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
