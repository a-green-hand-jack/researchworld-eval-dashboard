"""Check of the first-order (AMIP-style) influence formula for BT on Arena 55k: predicted vs exact-refit change of a
rank-gap functional phi = theta_i - theta_j after dropping the m comparisons with largest predicted influence.
Derivation (ours; Broderick et al. 2020 give the generic recipe): theta_hat(w) solves sum_n w_n * (-(y_n-p_n)) x_n + lam*theta = 0,
x_n = e_a - e_b, hence d theta/d w_n = H^{-1} (y_n-p_n) x_n, H = sum_n w_n p_n(1-p_n) x_n x_n^T + lam I.
For phi = c^T theta: psi_n = (H^{-1}c)^T x_n (y_n-p_n); dropping set S changes phi by about -sum_{n in S} psi_n.
Usage: python3 -I amip_check.py <datadir>"""
import sys, numpy as np
sys.path.insert(0, __file__.rsplit('/',1)[0])
from bt_checks import load, encode, fit_bt, hessian
D = sys.argv[1]; LAM = 1e-3
arena, _, _ = load(); names, ia, ib, y = encode(*arena); K = len(names); N = len(y)
w1 = np.ones(N); t = fit_bt(K, ia, ib, y, lam=LAM)
H, p = hessian(t, ia, ib, w1, LAM)
order = np.argsort(-t)
rng = np.random.default_rng(0)
for (r1, r2) in [(2, 3), (0, 4), (9, 10)]:
    i, j = order[r1], order[r2]; c = np.zeros(K); c[i], c[j] = 1, -1
    gap = t[i]-t[j]; u = np.linalg.solve(H, c); psi = (u[ia]-u[ib])*(y-p)
    print(f'\n== pair ranks {r1+1} vs {r2+1}: {names[i]} - {names[j]}, gap={gap:.4f}, N={N}')
    idx = np.argsort(-psi)  # drop largest psi first (they reduce phi most)
    print('   m   fraction  predicted_gap  exact_gap(refit)  random_drop_gap(mean of 10)  flipped_exact')
    first_pred = None; csum = np.cumsum(psi[idx])
    pred_flip_m = int(np.argmax(gap-csum < 0))+1 if (gap-csum < 0).any() else None
    for m in [10, 25, 50, 100, 200, 400, 800]:
        w = np.ones(N); w[idx[:m]] = 0
        te = fit_bt(K, ia, ib, y, w, lam=LAM)
        rd = []
        for _ in range(10):
            ww = np.ones(N); ww[rng.choice(N, m, replace=False)] = 0
            tr = fit_bt(K, ia, ib, y, ww, lam=LAM); rd.append(tr[i]-tr[j])
        print(f'  {m:4d}  {m/N:.5f}  {gap-csum[m-1]:+.4f}        {te[i]-te[j]:+.4f}          {np.mean(rd):+.4f}                {"yes" if te[i]-te[j]<0 else "no"}')
    # exact minimal m by bisection over the predicted ordering (upper bound on the true minimum)
    lo, hi = 1, 20000
    def flipped(m):
        w = np.ones(N); w[idx[:m]] = 0; te = fit_bt(K, ia, ib, y, w, lam=LAM); return te[i]-te[j] < 0
    if flipped(hi):
        while hi-lo > 1:
            mid = (lo+hi)//2
            if flipped(mid): hi = mid
            else: lo = mid
        print(f'   exact refit: smallest m along influence order that flips the pair = {hi} ({hi/N:.5f} of N); first-order prediction = {pred_flip_m}')
    else:
        print('   no flip within 20000 drops')
