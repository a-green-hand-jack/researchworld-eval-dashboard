"""One replicate: search on D, then every reporting method M0-M5 on the same search run. Truth supplied as a vector `th`
(exact theta_c in T0; fresh-item means in T1)."""
import numpy as np
import lib

def run_methods(Yd, th, proc, levels, rng, base=0, opts=None):
    """Yd: K x n 0/1 matrix of the search set; th: length-K true accuracies. Returns (run_row, [method_rows])."""
    o = dict(m1_fracs=(0.2, 0.5, 0.8), m2_folds=5, m3_B=0, m4=True, m5=True, boot_beta=0.005); o.update(opts or {})
    K, n = Yd.shape
    nb = lib.neighbors(levels) if proc == "greedy" else None
    pf = lib.PROC[proc]; pkw = dict(levels=levels, nb=nb)
    chat, kev = pf(Yd, rng, **pkw)
    R0 = float(Yd[chat].mean()); kd = int(Yd[chat].sum())
    base_D = float(Yd[base].mean())
    run = dict(K_eval=kev, chosen_config=chat, reported_naive=R0, theta=float(th[chat]), theta_pop_mean=float(th.mean()),
               theta_best=float(th.max()), theta_base=float(th[base]), baseline_reported=base_D,
               tuned_untuned_fresh_gain=float(th[chat] - th[base]))
    rows = []
    def add(method, est, lo=np.nan, hi=np.nan, items_search=n, items_report=n, target="theta_chat", theta_t=None, base_est=base_D, **kw):
        rows.append(dict(method=method, estimate=float(est), lo=float(lo), hi=float(hi), level=0.95 if np.isfinite(lo) else np.nan,
                         items_search=items_search, items_report=items_report, target=target,
                         theta_target=float(th[chat] if theta_t is None else theta_t), theta_chat=float(th[chat]),
                         base_est=float(base_est), theta_base=float(th[base]), **kw))
    lo, hi = lib.wilson(kd, n); add("M0", R0, lo, hi)
    # M1 holdout
    for f in o["m1_fracs"]:
        perm = rng.permutation(n); ns = max(2, int(round(f * n))); s_idx, r_idx = perm[:ns], perm[ns:]
        c1, _ = pf(Yd[:, s_idx], rng, **pkw); k1 = int(Yd[c1, r_idx].sum()); nr = len(r_idx)
        lo, hi = lib.wilson(k1, nr)
        add(f"M1_f{f}", k1 / nr, lo, hi, items_search=ns, items_report=nr, theta_t=th[c1], base_est=float(Yd[base, r_idx].mean()), calib_split="")
    # M2 cross-fitting
    kf = o["m2_folds"]
    if kf:
        folds = np.array_split(rng.permutation(n), kf); corr = 0; tot = 0; tt = []
        for j in range(kf):
            tr = np.concatenate([folds[i] for i in range(kf) if i != j]); cj, _ = pf(Yd[:, tr], rng, **pkw)
            corr += Yd[cj, folds[j]].sum(); tot += len(folds[j]); tt.append(th[cj])
        est = corr / tot; lo, hi = lib.wilson(int(corr), tot)
        add("M2", est, lo, hi, items_search=int(n * (kf - 1) / kf), items_report=n, target="E_theta_procedure", theta_t=float(np.mean(tt)))
    # M3 bootstrap
    if o["m3_B"]:
        e1, e632, _ = lib.boot_opt(Yd, pf, rng, B=o["m3_B"], pkw=pkw)
        add("M3_opt", e1); add("M3_632", e632)
    # M4 selection-aware
    if o["m4"]:
        lo, hi, q1 = lib.simultaneous_ci(Yd, chat, rng, beta=o["boot_beta"])
        add("M4_simult", R0, lo, hi)
        if proc == "exhaustive":   # conditional / hybrid inference assume the winner is the argmax of the reported means: not applicable to halving / greedy
            try:
                cl, ch, cm = lib.cond_ci(Yd, chat, rng=rng); add("M4_cond", cm, cl, ch)
                hl, hh, hm = lib.cond_ci(Yd, chat, hybrid_beta=o["boot_beta"], q_first=q1, rng=rng); add("M4_hybrid", hm, hl, hh)
            except Exception:  # numerical failure is recorded as missing, not hidden
                add("M4_cond", np.nan); add("M4_hybrid", np.nan)
    if o["m5"]:
        e, l, h = lib.eb_shrink(Yd, chat); add("M5_eb", e, l, h)
        add("M5_ladder", lib.ladder(Yd, rng))
        add("M5_ladder_se", lib.ladder(Yd, rng, eta=0.5 / np.sqrt(n)))
    return run, rows
