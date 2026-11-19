"""Offline research utility (not used by the RPC evaluator): width x train-fraction sweep.

Drives ``program.handle`` through the same reset/load_train/train/predict operations as the
evaluator and measures, per run,
    t_mem = first checkpoint with train_acc >= 0.99
    t_gen = first checkpoint with val_acc  >= 0.99   (censored if never reached)
    delay = t_gen - t_mem                            (undefined / censored when t_gen is censored)
It then estimates the critical width d*(f) (smallest width reaching train acc >= 0.99 in a
majority of seeds), fits log d* vs log f with a bootstrap CI (prediction P2), and reports
bootstrap 95% CIs of t_mem, t_gen and delay per cell. Censored runs are never counted as
successes and are never imputed.

Usage:  python grok_sweep.py --smoke            (tiny grid)
        python grok_sweep.py --out sweep.json   (full grid; tens of CPU hours)
"""

import argparse
import base64
import json

import numpy as np

import program

TARGET = 0.99


def _arr(a):
    return program._encode(np.asarray(a))


def make_split(p, train_fraction, seed):
    a, b = np.meshgrid(np.arange(p), np.arange(p), indexing="ij")
    pairs = np.stack([a.ravel(), b.ravel()], axis=1)
    labels = (pairs[:, 0] + pairs[:, 1]) % p
    perm = np.random.RandomState(seed).permutation(len(pairs))
    n_train = int(round(train_fraction * len(pairs)))
    tr, va = perm[:n_train], perm[n_train:]
    return pairs[tr], labels[tr], pairs[va], labels[va]


def run_one(p, d, train_fraction, seed, lr=1e-3, wd=1.0, max_steps=20000, every=50, post=500,
            out_exp=None, unembed_init=None):
    # out_exp switch: 0 = standard parametrization, >0 = width-aware (muP-like) logit scale.
    if out_exp is not None:
        program.OUT_EXP = out_exp
    if unembed_init is not None:
        program.UNEMBED_INIT = unembed_init
    xtr, ytr, xva, yva = make_split(p, train_fraction, seed)
    program.handle({"op": "reset", "seed": seed, "modulus": p, "operation": "add", "d_model": d,
                    "n_heads": 4, "learning_rate": lr, "betas": [0.9, 0.98],
                    "weight_decay": wd, "full_batch": True, "max_steps": max_steps})
    rows = np.concatenate([xtr, ytr[:, None]], axis=1)
    program.handle({"op": "load_train", "rows": _arr(rows)})

    def acc(x, y):
        r = program.handle({"op": "predict", "pairs": _arr(x)})
        pred = np.frombuffer(base64.b64decode(r["predictions"]["data"]), dtype="<i2")
        return float((pred == y).mean())

    t_mem = t_gen = None
    step = 0
    while step < max_steps:
        program.handle({"op": "train", "steps": every})
        step += every
        if t_mem is None and acc(xtr, ytr) >= TARGET:
            t_mem = step
        if acc(xva, yva) >= TARGET:
            t_gen = step
            break
    censored = t_gen is None
    delay = None if (censored or t_mem is None) else t_gen - t_mem  # delay = t_gen - t_mem
    n_params = sum(q.numel() for q in program._STATE["model"].parameters())
    return {"p": p, "d": d, "train_fraction": train_fraction, "seed": seed, "wd": wd, "lr": lr,
            "out_exp": program.OUT_EXP, "unembed_init": program.UNEMBED_INIT,
            "t_mem": t_mem, "t_gen": t_gen, "delay": delay, "censored": censored,
            "mem_reached": t_mem is not None, "n_params": n_params,
            "final_val_acc": acc(xva, yva)}


def bootstrap_ci(x, stat=np.median, n=2000, seed=0):
    x = np.asarray([v for v in x if v is not None], dtype=float)
    if len(x) == 0:
        return [None, None, None]
    rs = np.random.RandomState(seed)
    boots = [stat(rs.choice(x, len(x))) for _ in range(n)]
    return [float(stat(x)), float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]


def critical_width(runs, f, widths):
    """Smallest width whose majority of seeds reach train acc >= 0.99 at fraction f."""
    for d in sorted(widths):
        cell = [r for r in runs if r["d"] == d and r["train_fraction"] == f]
        if cell and np.mean([r["mem_reached"] for r in cell]) > 0.5:
            return d
    return None


def critical_width_slope(runs, fracs, widths, n=1000, seed=0):
    """Slope of log d* vs log f with a seed-bootstrap 95% CI (P2 predicts ~1)."""
    def slope(rs):
        pts = [(f, critical_width(rs, f, widths)) for f in fracs]
        pts = [(f, d) for f, d in pts if d is not None]
        if len(pts) < 2:
            return np.nan
        return float(np.polyfit(np.log([f for f, _ in pts]), np.log([d for _, d in pts]), 1)[0])
    rs_ = np.random.RandomState(seed)
    boots = []
    for _ in range(n):
        res = []
        for d in widths:
            for f in fracs:
                cell = [r for r in runs if r["d"] == d and r["train_fraction"] == f]
                if cell:
                    res += [cell[i] for i in rs_.randint(0, len(cell), len(cell))]
        boots.append(slope(res))
    boots = np.array([b for b in boots if not np.isnan(b)])
    ci = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))] if len(boots) else None
    return slope(runs), ci


def delay_slope(runs, widths, n=1000, seed=0):
    """Slope of log(delay) vs log(width) (median delay over non-censored seeds per width) with a
    seed-bootstrap 95% CI. Censored runs have no delay and are excluded (never imputed); the
    censored fraction per width is reported separately."""
    def slope(rs):
        pts = []
        for d in widths:
            dl = [r["delay"] for r in rs if r["d"] == d and r["delay"] is not None and r["delay"] > 0]
            if dl:
                pts.append((d, float(np.median(dl))))
        if len(pts) < 2:
            return np.nan
        return float(np.polyfit(np.log([d for d, _ in pts]), np.log([v for _, v in pts]), 1)[0])
    rs_ = np.random.RandomState(seed)
    boots = []
    for _ in range(n):
        res = []
        for d in widths:
            cell = [r for r in runs if r["d"] == d]
            if cell:
                res += [cell[i] for i in rs_.randint(0, len(cell), len(cell))]
        boots.append(slope(res))
    boots = np.array([b for b in boots if not np.isnan(b)])
    ci = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))] if len(boots) else None
    return slope(runs), ci


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default="sweep.json")
    ap.add_argument("--wd", type=float, default=1.0)
    ap.add_argument("--out_exp", type=float, nargs="+", default=[0.0, 1.0],
                    help="parametrizations to compare (0 = standard)")
    ap.add_argument("--unembed_init", type=float, nargs="+", default=[1.0],
                    help="unembed init multipliers to compare")
    args = ap.parse_args()
    widths = [16, 32] if args.smoke else [16, 32, 64, 128, 256]
    fracs = [0.3, 0.5] if args.smoke else [0.2, 0.3, 0.4, 0.5, 0.7]
    seeds = [0, 1] if args.smoke else [0, 1, 2, 3, 4]
    p, max_steps = (23, 500) if args.smoke else (97, 20000)
    configs = [(oe, ui) for oe in args.out_exp for ui in args.unembed_init]
    runs = []
    for oe, ui in configs:
        for d in widths:
            for train_fraction in fracs:
                for seed in seeds:
                    runs.append(run_one(p, d, train_fraction, seed, wd=args.wd, max_steps=max_steps,
                                        out_exp=oe, unembed_init=ui))
    # Per-parametrization ablation: per-width bootstrap CIs and delay-vs-width slope.
    param_summary = {}
    for oe, ui in configs:
        sub = [r for r in runs if r["out_exp"] == oe and r["unembed_init"] == ui]
        per_width = {}
        for d in widths:
            cell = [r for r in sub if r["d"] == d]
            per_width[str(d)] = {
                "t_mem": bootstrap_ci([r["t_mem"] for r in cell]),
                "t_gen": bootstrap_ci([r["t_gen"] for r in cell]),
                "delay": bootstrap_ci([r["delay"] for r in cell]),
                "censored_fraction": float(np.mean([r["censored"] for r in cell])),
                "mean_final_val_acc": float(np.mean([r["final_val_acc"] for r in cell])),
            }
        s, ci = delay_slope(sub, widths)
        param_summary[f"out_exp={oe},unembed_init={ui}"] = {
            "per_width": per_width, "log_delay_vs_log_width_slope": s, "slope_ci95": ci}
    # Critical-width analysis below uses the last configuration only.
    runs_all = runs
    runs = [r for r in runs if r["out_exp"] == configs[-1][0] and r["unembed_init"] == configs[-1][1]]
    summary = {}
    for d in widths:
        for f in fracs:
            cell = [r for r in runs if r["d"] == d and r["train_fraction"] == f]
            summary[f"d={d},f={f}"] = {
                "t_mem": bootstrap_ci([r["t_mem"] for r in cell]),
                "t_gen": bootstrap_ci([r["t_gen"] for r in cell]),
                "delay": bootstrap_ci([r["delay"] for r in cell]),
                "censored_fraction": float(np.mean([r["censored"] for r in cell])),
            }
    slope, ci = critical_width_slope(runs, fracs, widths)
    out = {"runs": runs_all, "param_summary": param_summary, "summary": summary,
           "critical_width": {str(f): critical_width(runs, f, widths) for f in fracs},
           "log_dstar_vs_log_f_slope": slope, "slope_ci95": ci}
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
