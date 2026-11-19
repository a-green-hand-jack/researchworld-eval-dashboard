"""C4 (optional): can a cheap per-instance diagnostic tell which instances a single run is unreliable for?

usage: python3 analysis/diagnostic.py [raw_dir] [out_dir]
Target: instance is 'unreliable' at (k, tau=0.9) if P_runs[top-k set == phi* top-k set] < 0.9, evaluated on the runs NOT
used by the diagnostic (runs n_diag..R-1). Diagnostics:
  own_margin : gap between the k-th and (k+1)-th |attribution| of ONE run (run 0), relative to its largest |attribution|
               (needs only the single run; larger gap => more reliable)
  repeat_z   : from n_diag runs (0..n_diag-1): z = gap of the mean vector / sd of the gap across the runs
               (large z => reliable); n_diag in {3, 5}
  repeat_pmatch : parametric-bootstrap estimate of P(single-run top-k set == top-k set of the mean of the n_diag runs),
               drawing N(mean, diag(sd^2)) 200 times
Scores are evaluated by ROC AUC for flagging unreliable instances (pooled within cell x explainer x budget; AUC=0.5 chance) and
by an operating curve (tables/operating_curve.csv: flag an instance when own_margin < t or repeat_z < t; false-adequate rate =
share of unreliable instances among the unflagged, with Wilson CI) and by calibration of repeat_pmatch against the held-out match probability (Brier skill, mean abs error).
"""
import glob, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
import metrics as M

raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results", "raw")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "results", "tables")
rng = np.random.RandomState(11)


def auc(score, label):
    """P(score of a positive > score of a negative), ties 1/2; label=1 means 'flag this instance'."""
    s, y = np.asarray(score, float), np.asarray(label, bool)
    if y.all() or (~y).all():
        return np.nan
    pos, neg = s[y], s[~y]
    return float(((pos[:, None] > neg[None]).mean() + 0.5 * (pos[:, None] == neg[None]).mean()))


def boot_auc(score, label, B=500):
    n = len(score); v = []
    for _ in range(B):
        ix = rng.randint(0, n, n); a = auc(np.asarray(score)[ix], np.asarray(label)[ix])
        if not np.isnan(a):
            v.append(a)
    return (np.quantile(v, .025), np.quantile(v, .975)) if len(v) > 20 else (np.nan, np.nan)


res = []; ops = []
THR = {"own_margin": (0.02, 0.05, 0.1, 0.2, 0.3), "repeat_z": (1, 2, 3, 5)}


def wilson(x, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = x / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(c - h, 0.0), min(c + h, 1.0))


for fref in sorted(glob.glob(f"{raw}/*__ref.npz")):
    cell = os.path.basename(fref).rsplit("__", 1)[0]; ds, model = cell.split("__")
    ref = np.load(fref)["ref"]; N, d = ref.shape
    for ex in ("kernel", "perm"):
        f = f"{raw}/{cell}__{ex}.npz"
        if not os.path.exists(f):
            continue
        z = np.load(f); phi = z["phi"]; rows = z["rows"].mean((0, 2)); R = phi.shape[2]
        for b in range(phi.shape[1]):
            for k in (1, 3):
                if k >= d:
                    continue
                for nd in (3, 5):
                    sc = {"own_margin": [], "repeat_z": [], "repeat_pmatch": []}; emp = []
                    for i in range(N):
                        Sr = M.topk_ind(ref[i][None], k)[0]
                        emp.append((M.topk_ind(phi[i, b, nd:], k) == Sr).all(1).mean())
                        a = np.sort(np.abs(phi[i, b, 0]))[::-1]
                        sc["own_margin"].append((a[k - 1] - a[k]) / (a[0] + 1e-12))
                        P = phi[i, b, :nd]; mu = P.mean(0); sd = P.std(0, ddof=1) + 1e-12
                        order = np.argsort(-np.abs(mu))
                        gap = np.abs(P[:, order[k - 1]]) - np.abs(P[:, order[k]])
                        sc["repeat_z"].append((np.abs(mu[order[k - 1]]) - np.abs(mu[order[k]])) / (gap.std(ddof=1) + 1e-12))
                        draws = mu + sd * rng.randn(200, d)
                        sc["repeat_pmatch"].append((M.topk_ind(draws, k) == M.topk_ind(mu[None], k)[0]).all(1).mean())
                    emp = np.array(emp); bad = emp < 0.9
                    for name, s in sc.items():
                        if name == "own_margin" and nd == 5:
                            continue  # single-run diagnostic does not depend on n_diag
                        s = np.array(s)
                        if not (name == "repeat_pmatch" or (name == "own_margin" and nd != 3)):
                            for t in THR[name]:
                                fl = s < t; acc = ~fl; na = int(acc.sum()); xb = int((bad & acc).sum()); lo_, hi_ = wilson(xb, na)
                                ops.append(dict(dataset=ds, model=model, d=d, explainer=ex, budget=int(z["budgets"][b]), rows=rows[b], k=k,
                                                diagnostic=name, n_diag=(1 if name == "own_margin" else nd), threshold=t, n_inst=N,
                                                frac_unreliable_overall=bad.mean(), frac_flagged=fl.mean(), n_accepted=na, n_false_adequate=xb, n_reliable=int((~bad).sum()),
                                                n_reliable_retained=int(((~bad) & acc).sum()), adequate_retained=((~bad) & acc).sum() / max((~bad).sum(), 1),
                                                false_adequate=(xb / na if na else np.nan), false_adequate_lo=lo_, false_adequate_hi=hi_,
                                                reliable_flagged=((~bad) & fl).sum() / max((~bad).sum(), 1)))
                        a = auc(-s, bad); lo, hi = boot_auc(-s, bad)
                        r = dict(dataset=ds, model=model, d=d, explainer=ex, budget=int(z["budgets"][b]), rows=rows[b], k=k,
                                 n_diag=(1 if name == "own_margin" else nd), diagnostic=name, n_inst=N, frac_unreliable=bad.mean(), auc=a, auc_lo=lo, auc_hi=hi)
                        if name == "repeat_pmatch":
                            r["mae_calibration"] = float(np.abs(s - emp).mean())
                            r["brier_skill"] = float(1 - ((s - emp) ** 2).mean() / max(((emp.mean() - emp) ** 2).mean(), 1e-12))
                        res.append(r)
pd.DataFrame(res).to_csv(f"{out}/diagnostic.csv", index=False)
O = pd.DataFrame(ops); O.to_csv(f"{out}/operating_curve.csv", index=False)
# deployer summary: library-default budget (2d + 2048 nominal) on the d > 10 cells; two sub-default budgets on the d <= 10 cells (where the
# default is exact and not in the grid).  Instances are pooled over the cells of a group (descriptive; cells are not independent replicates).
O = O[~O.dataset.str.endswith("_logit")]
SUB = {"pima": (80, 160), "gmsc": (100, 500), "acs": (100, 500)}
O["group"] = np.where(O.d > 10, np.where(O.budget == 2 * O.d + 2048, "d>10 default budget", ""),
                      np.where(O.apply(lambda r: r.budget in SUB.get(r.dataset, ()), axis=1), "d<=10 sub-default budgets (pima 80/160, gmsc+acs 100/500)", ""))
G = O[O.group != ""].groupby(["group", "explainer", "k", "diagnostic", "n_diag", "threshold"])
rows_ = []
for key, g in G:
    na, xb = g.n_accepted.sum(), g.n_false_adequate.sum(); lo_, hi_ = wilson(int(xb), int(na)); nr = g.n_reliable.sum()
    rows_.append(dict(zip(("group", "explainer", "k", "diagnostic", "n_diag", "threshold"), key), n_cell_budgets=len(g), n_inst=int(g.n_inst.sum()),
                      frac_unreliable_overall=(g.frac_unreliable_overall * g.n_inst).sum() / g.n_inst.sum(), frac_flagged=1 - na / g.n_inst.sum(),
                      false_adequate=xb / na if na else np.nan, false_adequate_lo=lo_, false_adequate_hi=hi_,
                      adequate_retained=g.n_reliable_retained.sum() / max(nr, 1)))
pd.DataFrame(rows_).to_csv(f"{out}/operating_curve_summary.csv", index=False)
print(len(res), "rows")
