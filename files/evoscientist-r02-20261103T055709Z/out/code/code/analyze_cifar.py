"""Analysis of CIFAR-10H results -> tables + figure. Usage: python code/analyze_cifar.py [raw_csv]"""
import sys, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

raw = sys.argv[1] if len(sys.argv) > 1 else "results/cifar_raw.csv"
d = pd.read_csv(raw)
LAB = {"l2": r"$\ell_2$", "l1": "TV", "linf": r"$\ell_\infty$", "hell": "Hellinger", "aitch": "Aitch(1e-2)",
       "aitch@0.001": "Aitch(1e-3)", "aitch@0.1": "Aitch(1e-1)", "kl": "KL"}
SC = [s for s in LAB if s in d.score.unique()]
plt.rcParams.update({"font.size": 8, "figure.dpi": 150})
print("predictor accuracy vs hard labels:", d.groupby("seed").acc.first().round(4).to_dict(), " temperature (mean over splits):", d.groupby("seed").T.mean().round(3).to_dict())
print("reps per seed:", d.groupby("seed").rep.nunique().to_dict())

COLS = ["cov", "mass", "mass_fin", "inf_frac", "wsc_conf", "wsc_ent", "maxdev_conf", "maxdev_ent"]
rows = []
for (st, nc, sc, m), s in d.groupby(["setting", "ncal", "score", "method"]):
    r = dict(setting=st, ncal=nc, score=sc, method=m)
    for col in COLS:
        g = s.groupby("seed")[col].agg(["mean", "sem"])           # split-level SE within each CNN seed
        r[col] = g["mean"].mean(); r[col + "_hw"] = 1.96 * np.sqrt((g["sem"] ** 2).sum()) / len(g)
        r[col + "_seed0"] = g["mean"].iloc[0]; r[col + "_seed1"] = g["mean"].iloc[1] if len(g) > 1 else np.nan
    rows.append(r)
R = pd.DataFrame(rows); R.to_csv("results/tables/cifar_summary.csv", index=False)
pd.set_option("display.width", 250)
fm = lambda mu, hw: [f"{a:.3f}±{b:.3f}" for a, b in zip(mu, hw)]
for st in ["iid", "soft", "hard"]:
    q = R[(R.setting == st) & (R.ncal == 500) & (R.method == "plain")]
    print(f"\n== {st}, ncal=500, plain =="); print(pd.DataFrame({"score": q.score, "cov": fm(q["cov"], q.cov_hw), "mass": fm(q.mass, q.mass_hw),
          "wsc_conf": fm(q.wsc_conf, q.wsc_conf_hw), "wsc_ent": fm(q.wsc_ent, q.wsc_ent_hw)}).to_string(index=False))
    for s in ["l2", "kl"]:
        q = R[(R.setting == st) & (R.ncal == 500) & (R.score == s)]
        print(f"-- methods, {s}, {st}"); print(q[["method", "cov", "cov_hw", "mass", "mass_fin", "inf_frac", "wsc_conf", "wsc_ent", "maxdev_ent"]].round(3).to_string(index=False))
# sign consistency across the two CNN seeds for the score ranking by mass (iid, plain)
q = R[(R.setting == "iid") & (R.ncal == 500) & (R.method == "plain")].set_index("score")
print("\nrank of mass by score per seed (iid, n=500):"); print(pd.DataFrame({"seed0": q.mass_seed0.rank(), "seed1": q.mass_seed1.rank(), "mass0": q.mass_seed0.round(4), "mass1": q.mass_seed1.round(4)}))
# paired split-level comparison: mass_{score} - mass_{kl}
w = d[(d.setting == "iid") & (d.ncal == 500) & (d.method == "plain")].pivot_table(index=["seed", "rep"], columns="score", values="mass")
print("\npaired mass diff vs KL (iid, n=500), mean±SE over splits, per seed")
for sd in sorted(d.seed.unique()):
    x = w.loc[sd]; print(sd, {s: f"{(x[s]-x['kl']).mean():+.4f}±{(x[s]-x['kl']).sem():.4f}" for s in SC if s != "kl"})

fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.5))
for j, (st, ttl) in enumerate([("iid", "exchangeable"), ("soft", "soft shift"), ("hard", "hard shift")]):
    q = R[(R.setting == st) & (R.ncal == 500) & (R.method == "plain")].set_index("score").loc[SC]
    ax[0].errorbar(np.arange(len(SC)) + (j - 1) * .22, q["cov"], q.cov_hw, fmt="os^"[j], ms=3, label=ttl)
    ax[1].errorbar(np.arange(len(SC)) + (j - 1) * .22, q["mass"], q.mass_hw, fmt="os^"[j], ms=3, label=ttl)
for a, yl in zip(ax[:2], ["marginal coverage (plain)", "mass of reference set in prediction set"]):
    a.set_xticks(range(len(SC))); a.set_xticklabels([LAB[s].replace("$", "") for s in SC], rotation=60, fontsize=6); a.set_ylabel(yl)
ax[0].axhline(0.9, c="k", lw=.5); ax[0].legend(fontsize=6); ax[1].set_yscale("log")
for m, mk in zip(["plain", "norm", "mond"], "ovs"):
    q = R[(R.setting == "iid") & (R.score == "l2") & (R.method == m)].sort_values("ncal")
    ax[2].errorbar(q.ncal, q.wsc_ent, q.wsc_ent_hw, fmt=mk + "-", ms=3, label=m)
ax[2].set_xscale("log"); ax[2].set_xlabel("calibration size"); ax[2].set_ylabel("worst entropy-slice coverage ($\\ell_2$)"); ax[2].legend(fontsize=6)
plt.tight_layout(); plt.savefig("figs/cifar_main.pdf"); plt.savefig("scratch/cifar_main.png", dpi=110); plt.close()
print("ok")
