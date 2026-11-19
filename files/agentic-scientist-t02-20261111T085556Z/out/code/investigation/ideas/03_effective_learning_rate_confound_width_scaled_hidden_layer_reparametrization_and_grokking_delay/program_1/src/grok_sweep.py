"""Offline research utility (not used by the RPC evaluator): hidden-layer reparametrization sweep.

Drives ``program.handle`` through the same reset/load_train/train/predict operations as the
evaluator and measures, per run (width x seed x hidden_exp at a fixed train fraction),
    t_mem = first checkpoint with train_acc >= 0.99
    t_gen = first checkpoint with val_acc  >= 0.99   (censored if never reached)
    delay = t_gen - t_mem                            (undefined / censored when t_gen is censored)
It reports bootstrap 95% CIs of t_mem, t_gen and delay per width and hidden_exp, log-log slopes
(np.polyfit(np.log(width), np.log(t), 1), uncensored runs only, censored counts shown), and a
bootstrap CI of the slope difference between hidden_exp = 0 and each other value (P1: t_mem,
P2: delay). Censored runs are never counted as successes and are never imputed.
(critical_width* / delay_slope helpers are kept from the earlier width x fraction sweep.)

Usage:  python grok_sweep.py --smoke            (tiny grid)
        python grok_sweep.py --out sweep.json   (full grid; several CPU hours)
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
            out_exp=None, unembed_init=None, hidden_exp=None):
    # out_exp: logit scale exponent; hidden_exp: hidden-matrix multiplier exponent (0 = standard).
    if out_exp is not None:
        program.OUT_EXP = out_exp
    if unembed_init is not None:
        program.UNEMBED_INIT = unembed_init
    if hidden_exp is not None:
        program.HIDDEN_EXP = hidden_exp
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
            "out_exp": program.OUT_EXP, "hidden_exp": program.HIDDEN_EXP, "unembed_init": program.UNEMBED_INIT,
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


def _slope_pts(runs, widths, key):
    """(width, median of `key` over runs with a defined, positive value) per width; censored runs
    (key is None) are excluded, never imputed."""
    pts = []
    for d in widths:
        vals = [r[key] for r in runs if r["d"] == d and r[key] is not None and r[key] > 0]
        if vals:
            pts.append((d, float(np.median(vals))))
    return pts


def loglog_slope(runs, widths, key):
    pts = _slope_pts(runs, widths, key)
    if len(pts) < 2:
        return float("nan")
    return float(np.polyfit(np.log([d for d, _ in pts]), np.log([v for _, v in pts]), 1)[0])


def _resample(runs, widths, rs):
    out = []
    for d in widths:
        cell = [r for r in runs if r["d"] == d]
        if cell:
            out += [cell[i] for i in rs.randint(0, len(cell), len(cell))]
    return out


def bootstrap_slope(runs, widths, key, n=1000, seed=0):
    """Seed-bootstrap 95% CI of the log-log slope of `key` vs width."""
    rs = np.random.RandomState(seed)
    boots = np.array([loglog_slope(_resample(runs, widths, rs), widths, key) for _ in range(n)])
    boots = boots[~np.isnan(boots)]
    ci = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))] if len(boots) else None
    return loglog_slope(runs, widths, key), ci


def bootstrap_slope_diff(runs_a, runs_b, widths, key, n=1000, seed=0):
    """Bootstrap CI of slope(runs_b) - slope(runs_a) (independent resampling of each arm)."""
    rs = np.random.RandomState(seed)
    diffs = np.array([loglog_slope(_resample(runs_b, widths, rs), widths, key)
                      - loglog_slope(_resample(runs_a, widths, rs), widths, key) for _ in range(n)])
    diffs = diffs[~np.isnan(diffs)]
    ci = [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))] if len(diffs) else None
    return loglog_slope(runs_b, widths, key) - loglog_slope(runs_a, widths, key), ci


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out", default="sweep.json")
    ap.add_argument("--wd", type=float, default=1.0)
    ap.add_argument("--train_fraction", type=float, default=0.3)
    ap.add_argument("--hidden_exp", type=float, nargs="+", default=[0.0, 0.5, 1.0],
                    help="hidden-layer multiplier exponents to compare (0 = standard)")
    ap.add_argument("--out_exp", type=float, default=None, help="override program.OUT_EXP")
    ap.add_argument("--unembed_init", type=float, default=None, help="override program.UNEMBED_INIT")
    ap.add_argument("--seeds", type=int, default=4)
    args = ap.parse_args()
    widths = [16, 32] if args.smoke else [16, 32, 64, 128, 256]
    seeds = list(range(2 if args.smoke else args.seeds))
    p, max_steps = (23, 500) if args.smoke else (97, 20000)
    runs = []
    for he in args.hidden_exp:
        for d in widths:
            for seed in seeds:
                runs.append(run_one(p, d, args.train_fraction, seed, wd=args.wd, max_steps=max_steps,
                                    out_exp=args.out_exp, unembed_init=args.unembed_init,
                                    hidden_exp=he))
    summary, by_he = {}, {}
    for he in args.hidden_exp:
        sub = [r for r in runs if r["hidden_exp"] == he]
        by_he[he] = sub
        per_width = {}
        for d in widths:
            cell = [r for r in sub if r["d"] == d]
            per_width[str(d)] = {
                "t_mem": bootstrap_ci([r["t_mem"] for r in cell]),
                "t_gen": bootstrap_ci([r["t_gen"] for r in cell]),
                "delay": bootstrap_ci([r["delay"] for r in cell]),
                "censored_fraction": float(np.mean([r["censored"] for r in cell])),
                "n_censored": int(sum(r["censored"] for r in cell)), "n": len(cell),
                "mean_final_val_acc": float(np.mean([r["final_val_acc"] for r in cell])),
            }
        slopes = {}
        for key in ("t_mem", "t_gen", "delay"):
            s, ci = bootstrap_slope(sub, widths, key)
            slopes[key] = {"slope": s, "ci95": ci}
        summary[f"hidden_exp={he}"] = {"per_width": per_width, "loglog_slopes": slopes}
    # Slope differences relative to hidden_exp = 0 (P1: t_mem; P2: delay).
    slope_diff = {}
    if 0.0 in by_he:
        for he in args.hidden_exp:
            if he == 0.0:
                continue
            slope_diff[f"hidden_exp={he}-vs-0"] = {
                key: dict(zip(("diff", "ci95"), bootstrap_slope_diff(by_he[0.0], by_he[he], widths, key)))
                for key in ("t_mem", "t_gen", "delay")}
    out = {"args": vars(args), "runs": runs, "summary": summary, "slope_diff": slope_diff}
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
