"""Flip-budget experiments for Bradley-Terry leaderboard adjacent-pair stability.

Six conditions (from the experiment plan) are evaluated independently per
(dataset, seed):

  DARTS                                      influence-guided greedy flip search
  Random Search                              random-order flip search
  bootstrap_ci_overlap_and_flip_probability  budget implied by bootstrap flip probability / CI
  wald_se_bt_fisher_information              budget implied by Wald z and Fisher information
  random_flip_budget_baseline                random flips on a (coarser) grid
  dropping_data_amip_influence_baseline      greedy data-dropping by influence (AMIP-style)

primary_metric (maximize) = mean over adjacent pairs of log2(N / k), where k is
the estimated minimal edit budget to reverse the adjacent rank. Larger = a
smaller budget relative to N = a MORE FRAGILE leaderboard as seen by that
method. Budgets that could not flip within the cap are censored at the cap
(and counted/reported), so a method that fails to find flips scores LOWER.
success_rate = fraction of pairs flipped within the cap.
"""
import time
import math
import numpy as np

from models import fit_bt, adjacent_pairs
from data import (subsample_fraction, load_all)
from experiment_config import CONDITIONS


# ------------------------------------------------------------------ helpers
def _gap(theta, a, b):
    return theta[a] - theta[b]


def _fit(data, y, hp, theta0=None):
    return fit_bt(data.to_counts(y=y), hp['bt_l2'], hp['bt_max_iter'], hp['bt_tol'], theta0=theta0)


def _supporting_records(data, a, b):
    """Decisive records that support a > b: a wins (vs anyone) or b loses (vs anyone)."""
    ia, ib, y = data.ia, data.ib, data.y
    a_win = ((ia == a) & (y == 1.0)) | ((ib == a) & (y == 0.0))
    b_loss = ((ia == b) & (y == 0.0)) | ((ib == b) & (y == 1.0))
    return np.where(a_win | b_loss)[0]


def _contrast_u(model, W, M, a, b):
    e = np.zeros(M)
    e[a], e[b] = 1.0, -1.0
    return model.fisher_cov(W) @ e


def _influence_flip(data, u, y):
    """First-order change in gap theta_a - theta_b from flipping each record."""
    d = 1.0 - 2.0 * y
    return d * (u[data.ia] - u[data.ib])


def _influence_drop(data, u, theta, y):
    """First-order change in gap from removing each record (score residual r)."""
    p = 1.0 / (1.0 + np.exp(-(theta[data.ia] - theta[data.ib])))
    r = y - p
    return -r * (u[data.ia] - u[data.ib])


# ------------------------------------------------------------------ budget routines
def greedy_flip_budget(data, a, b, hp, deadline, mode='flip'):
    """Greedy influence-guided search for the smallest edit set reversing a>b.

    mode='flip' (DARTS): flip supporting decisive records (y -> 1-y).
    mode='drop' (AMIP):  remove supporting records from the fit.
    Returns an upper bound on the minimal budget, or inf if not reached.
    """
    y = data.y.copy()
    kmax = int(hp['max_budget_frac'] * data.N)
    W = data.to_counts(y=y)
    th, model = fit_bt(W, hp['bt_l2'], hp['bt_max_iter'], hp['bt_tol'])
    if _gap(th, a, b) <= 0.0:
        return 0
    cand_mask = np.zeros(data.N, dtype=bool)
    cand_mask[_supporting_records(data, a, b)] = True
    used = np.zeros(data.N, dtype=bool)
    keep = np.ones(data.N, dtype=bool)
    k = 0
    while k < kmax:
        if time.time() > deadline:
            return float('inf')
        batch = hp['adv_batch_small'] if k < hp['adv_k_exact_max'] else hp['adv_batch_large']
        batch = min(batch, kmax - k)
        u = _contrast_u(model, W, data.M, a, b)
        if mode == 'flip':
            delta = _influence_flip(data, u, y)
        else:
            delta = _influence_drop(data, u, th, y)
        # we want the most negative change in the gap
        delta = np.where(cand_mask & ~used & (y != 0.5), delta, np.inf)
        order = np.argsort(delta)[:batch]
        order = order[np.isfinite(delta[order])]
        if len(order) == 0 or delta[order[0]] >= 0.0:
            return float('inf')
        if mode == 'flip':
            y[order] = 1.0 - y[order]
            W = data.to_counts(y=y)
        else:
            keep[order] = False
            W = data.to_counts(idx=np.where(keep)[0])
        used[order] = True
        k += len(order)
        th, model = fit_bt(W, hp['bt_l2'], hp['bt_max_iter'], hp['bt_tol'], theta0=th)
        if _gap(th, a, b) <= 0.0:
            return float(k)
    return float('inf')


def random_search_budget(data, a, b, hp, rng, deadline, reps=None, grid_points=None):
    """Random-order flips of supporting records on a budget grid; median over reps."""
    reps = reps or hp['random_flip_reps']
    grid_points = grid_points or hp['random_grid_points']
    cand = _supporting_records(data, a, b)
    if len(cand) == 0:
        return float('inf')
    kmax = int(min(len(cand), hp['max_budget_frac'] * data.N))
    if kmax < 1:
        return float('inf')
    grid = np.unique(np.geomspace(1, kmax, grid_points).astype(int))
    ks = []
    for _ in range(reps):
        perm = rng.permutation(cand)
        found = float('inf')
        for k in grid:
            if time.time() > deadline:
                break
            y2 = data.y.copy()
            y2[perm[:k]] = 1.0 - y2[perm[:k]]
            th, _ = _fit(data, y2, hp)
            if _gap(th, a, b) <= 0.0:
                found = float(k)
                break
        ks.append(found)
    return float(np.median(ks))


def wald_budget(theta, model, W, data, a, b):
    """First-order (Wald) budget k ~ gap / typical per-record influence.

    Returns (k, z). Per-record influence is the mean of the top-quartile
    influences among supporting records (the c*z*sqrt(I) first-order law).
    """
    gap = _gap(theta, a, b)
    if gap <= 0:
        return 0.0, 0.0
    C = model.fisher_cov(W)
    var = C[a, a] + C[b, b] - 2.0 * C[a, b]
    z = gap / math.sqrt(max(var, 1e-12))
    u = _contrast_u(model, W, data.M, a, b)
    infl = np.abs(_influence_flip(data, u, data.y))
    cand = _supporting_records(data, a, b)
    if len(cand) == 0:
        return float('inf'), float(z)
    v = np.sort(infl[cand])[::-1]
    top = v[:max(1, len(v) // 4)]
    per = float(np.mean(top))
    if per <= 1e-12:
        return float('inf'), float(z)
    return float(gap / per), float(z)


def bootstrap_stats(data, a, b, hp, rng):
    """Flip probability and gap sd under iid bootstrap of records."""
    N = data.N
    gaps = []
    for _ in range(hp['n_bootstrap']):
        idx = rng.integers(0, N, N)
        th, _ = fit_bt(data.to_counts(idx=idx), hp['bt_l2'], hp['bt_max_iter'], hp['bt_tol'])
        gaps.append(_gap(th, a, b))
    gaps = np.asarray(gaps)
    return float((gaps <= 0).mean()), float(gaps.std(ddof=1))


def bootstrap_budget(data, gap, sd_boot, a, b):
    """Budget implied by the bootstrap sd: k ~ 0.5 * (gap / sd) * sqrt(n_support)."""
    cand = _supporting_records(data, a, b)
    n_rec = max(len(cand), 1)
    if sd_boot <= 1e-12:
        return float('inf')
    return float(max((gap / sd_boot) * math.sqrt(n_rec) * 0.5, 1.0))


# ------------------------------------------------------------------ per-condition runner
def _log2_frac(k, N, hp):
    """log2(N / k); infinite budgets are censored at max_budget_frac * N."""
    cap = hp['max_budget_frac'] * N
    k = cap if (not np.isfinite(k)) else min(max(k, 1.0), cap)
    return math.log2(N / k)


def run_condition(cond, data, hp, rng, deadline):
    """Returns list of per-pair budgets for one condition on one dataset."""
    W = data.to_counts()
    theta, model = fit_bt(W, hp['bt_l2'], hp['bt_max_iter'], hp['bt_tol'])
    pairs = adjacent_pairs(theta, hp['top_m'])
    budgets = []
    for (a, b) in pairs:
        if time.time() > deadline:
            break
        if cond == 'DARTS':
            k = greedy_flip_budget(data, a, b, hp, deadline, mode='flip')
        elif cond == 'dropping_data_amip_influence_baseline':
            k = greedy_flip_budget(data, a, b, hp, deadline, mode='drop')
        elif cond == 'Random Search':
            k = random_search_budget(data, a, b, hp, rng, deadline)
        elif cond == 'random_flip_budget_baseline':
            k = random_search_budget(data, a, b, hp, rng, deadline,
                                     reps=2, grid_points=max(6, hp['random_grid_points'] // 2))
        elif cond == 'wald_se_bt_fisher_information':
            k, _ = wald_budget(theta, model, W, data, a, b)
        elif cond == 'bootstrap_ci_overlap_and_flip_probability':
            _, sd = bootstrap_stats(data, a, b, hp, rng)
            k = bootstrap_budget(data, _gap(theta, a, b), sd, a, b)
        else:
            raise ValueError(cond)
        budgets.append(float(k))
    return budgets


def primary_metric(budgets, N, hp):
    if not budgets:
        return float('nan')
    return float(np.mean([_log2_frac(k, N, hp) for k in budgets]))


def success_rate(budgets, N, hp):
    if not budgets:
        return float('nan')
    cap = hp['max_budget_frac'] * N
    return float(np.mean([np.isfinite(k) and k <= cap for k in budgets]))


# ------------------------------------------------------------------ top-level experiment
def run_experiment(hp):
    t0 = time.time()
    budget = hp['time_budget_sec'] * hp['time_guard_frac']
    results = {'status': {}, 'per_seed': {}, 'success': {}, 'agg': {},
               'stopped_early': False}
    per_cond = {c: [] for c in CONDITIONS}
    per_cond_succ = {c: [] for c in CONDITIONS}

    for seed in hp['seeds']:
        rng = np.random.default_rng(seed)
        datasets, status = load_all(hp, rng)
        results['status'].update(status)
        for dname, data in datasets.items():
            if data.M < 3:
                continue
            d = data
            if d.N > hp['max_records_search']:
                d = subsample_fraction(data, hp['max_records_search'] / float(data.N), rng,
                                       hp['min_comparisons_per_model'])
            if d.M < 3:
                continue
            for cond in CONDITIONS:
                now = time.time()
                if now - t0 > budget:
                    results['stopped_early'] = True
                    break
                deadline = min(now + hp['per_run_cap_sec'], t0 + budget)
                crng = np.random.default_rng(1000 * seed + CONDITIONS.index(cond))
                budgets = run_condition(cond, d, hp, crng, deadline)
                val = primary_metric(budgets, d.N, hp)
                sr = success_rate(budgets, d.N, hp)
                n_inf = int(sum(1 for k in budgets if not np.isfinite(k)))
                print('condition=%s dataset=%s seed=%d primary_metric: %.4f '
                      'success_rate: %.3f (n_pairs=%d censored=%d N=%d M=%d)'
                      % (cond, dname, seed, val, sr, len(budgets), n_inf, d.N, d.M))
                results['per_seed'].setdefault(cond, {}).setdefault(dname, []).append(val)
                results['success'].setdefault(cond, {}).setdefault(dname, []).append(sr)
                per_cond[cond].append(val)
                per_cond_succ[cond].append(sr)
            if results['stopped_early']:
                break
        if results['stopped_early']:
            break

    print('')
    for cond in CONDITIONS:
        vals = np.array([v for v in per_cond[cond] if np.isfinite(v)])
        srs = np.array([v for v in per_cond_succ[cond] if np.isfinite(v)])
        if len(vals):
            m = float(vals.mean())
            s = float(vals.std(ddof=1)) if len(vals) > 1 else 0.0
        else:
            m, s = float('nan'), float('nan')
        sm = float(srs.mean()) if len(srs) else float('nan')
        results['agg'][cond] = dict(mean=m, std=s, n=int(len(vals)), success_rate=sm)
        print('condition=%s primary_metric_mean: %.4f primary_metric_std: %.4f '
              'success_rate_mean: %.3f' % (cond, m, s, sm))

    means = {c: results['agg'][c]['mean'] for c in CONDITIONS}
    ok = {c: v for c, v in means.items() if np.isfinite(v)}
    best = max(ok, key=ok.get) if ok else 'none'
    spread = (max(ok.values()) - min(ok.values())) if ok else float('nan')
    print('SUMMARY ' + ' | '.join('%s=%.4f' % (c, means[c]) for c in CONDITIONS)
          + ' | best=%s | spread=%.4f' % (best, spread))
    results['elapsed_sec'] = time.time() - t0
    return results