"""Synthetic populations with known E[Y|f] (C2): paired width ratio to M3 and coverage vs nonlinearity kappa, n, N, SNR.

Y = sqrt(1-kappa) f + sqrt(kappa) h(f) + eps (experiment-repo src/data.py synth_sampler). Base cell: tanh, kappa=0.5, SNR=1,
n=100, N=20n. Dotted: asymptotic M4/M3 ratio from the population floor (theory_check_synth_final.csv, pred_ratio_vs_M3).
Writes synthetic_kappa (all three kinds) and synthetic_factors (n, N, SNR; tanh and quadratic).
"""
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from common import *
from panels import *

setup()
df = summary("synth")
df[["_", "kind", "kappa", "snr", "tail"]] = df["dataset"].str.split(":", expand=True)
for c in ("kappa", "snr", "tail"):
    df[c] = df[c].astype(float)
chk = load("theory_check_synth_final.csv")
chk = chk[chk["method"] == M4]
M3 = "ppipp_pkg"
WM = ["ppi", "cal_lin", M4]           # cal_lin: cross-fitting with an affine map = pure cost of cross-fitting
CM = [M3, M4, "ppipp_jk", M4 + "_t"]
KIND = {"tanh": "$h$ = tanh (saturating)", "quad": "$h$ quadratic", "bin": "binary $Y$"}


def sub(tag, kind, **fix):
    d = df[(df["tag"] == tag) & (df["kind"] == kind)]
    for k, v in fix.items():
        d = d[d[k] == v]
    c = chk[(chk["tag"] == tag) & (chk["kind"] == kind)]
    for k, v in fix.items():
        c = c[c[k] == v]
    return d, c


def draw(axw, axc, d, c, xcol, log=False, ticks=None, tlabels=None, ylim=(0.85, 1.3), covlim=None):
    d = d.copy(); c = c.copy()
    if ticks is not None:
        mp = {v: i for i, v in enumerate(ticks)}
        d[xcol] = d[xcol].map(mp); c[xcol] = c[xcol].map(mp)
    c = c.sort_values(xcol)
    lo_all = min(d[d["method"].isin(WM)]["ratio_lo"].min(), c["pred_ratio_vs_M3"].min())
    ylim = (min(ylim[0], np.floor((lo_all - 0.02) * 20) / 20), ylim[1])
    wid_panel(axw, d, WM, xcol=xcol, log=log, jitter=0.03 if log else 0.0, ylim=ylim,
              floor=(c[xcol].values, c["pred_ratio_vs_M3"].values, METHODS[M4][1]))
    cov_panel(axc, d, CM, xcol=xcol, log=log, jitter=0.03 if log else 0.0)
    axc.set_ylim(*(covlim or (0.8, 1.0)))
    axc.set_yticks(np.arange(axc.get_ylim()[0], 1.0001, 0.05).round(2))
    if ticks is not None:
        cat_ticks([axw, axc], list(range(len(ticks))), rotation=0, labels=tlabels)


def finish(fig, axes, name, floor=True):
    seen = {}
    for ax in axes.ravel():
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            seen.setdefault(ll, hh)
    h, l = list(seen.values()), list(seen)
    h.append(FLOOR_H); l.append("asymptotic floor for M4")
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02), columnspacing=1.0, handletextpad=0.4)
    save(fig, name)
    plt.close(fig)


covlim = (max(0.5, np.floor((df[df["method"].isin(CM)]["cov_lo"].min() - 0.01) * 20) / 20), 1.0)
# (a) kappa
fig, axes = plt.subplots(2, 3, figsize=(TEXT_W, 3.0), sharex=True, squeeze=False)
for j, kind in enumerate(("tanh", "quad", "bin")):
    d, c = sub("kappa", kind)
    draw(axes[0, j], axes[1, j], d, c, "kappa", ylim=(0.8, 1.3), covlim=covlim)
    axes[0, j].set_title(KIND[kind], pad=2)
    axes[1, j].set_xlabel("nonlinearity $\\kappa$")
    axes[1, j].set_xticks([0, 0.25, 0.5, 0.75, 1.0]); axes[1, j].set_xticklabels(["0", ".25", ".5", ".75", "1"])
axes[0, 0].set_ylabel("width / M3"); axes[1, 0].set_ylabel("coverage")
fig.tight_layout(rect=(0, 0.13, 1, 1), h_pad=0.5, w_pad=1.2)
finish(fig, axes, "synthetic_kappa")

# (b) n, N, SNR
fig, axes = plt.subplots(4, 3, figsize=(TEXT_W, 5.0), squeeze=False)
for r, kind in enumerate(("tanh", "quad")):
    base = dict(kappa=0.5)
    d, c = sub("n", kind, **base)
    d = pd.concat([d, df[(df["tag"] == "kappa") & (df["kind"] == kind) & (df["kappa"] == 0.5) & (df["snr"] == 1)]])
    c = pd.concat([c, chk[(chk["tag"] == "kappa") & (chk["kind"] == kind) & (chk["kappa"] == 0.5)]])
    draw(axes[2 * r, 0], axes[2 * r + 1, 0], d, c, "n", log=True, ticks=None, ylim=(0.85, 1.3), covlim=covlim)
    cat_ticks([axes[2 * r, 0], axes[2 * r + 1, 0]], sorted(d["n"].unique()))
    d, c = sub("Nratio", kind, **base, n=100)
    Ns = [100, 500, 2000, 20000]
    d = pd.concat([d, df[(df["tag"] == "kappa") & (df["kind"] == kind) & (df["kappa"] == 0.5) & (df["snr"] == 1)]])
    c = pd.concat([c, chk[(chk["tag"] == "kappa") & (chk["kind"] == kind) & (chk["kappa"] == 0.5)]])
    d = d[d["n"] == 100]; c = c[c["n"] == 100]
    draw(axes[2 * r, 1], axes[2 * r + 1, 1], d, c, "N", ticks=Ns, tlabels=["$n$", "$5n$", "$20n$", "20000"], ylim=(0.85, 1.3), covlim=covlim)
    d, c = sub("snr", kind, **base)
    d = pd.concat([d, df[(df["tag"] == "kappa") & (df["kind"] == kind) & (df["kappa"] == 0.5) & (df["snr"] == 1)]])
    c = pd.concat([c, chk[(chk["tag"] == "kappa") & (chk["kind"] == kind) & (chk["kappa"] == 0.5)]])
    snrs = sorted(d["snr"].unique())
    draw(axes[2 * r, 2], axes[2 * r + 1, 2], d, c, "snr", log=True, ylim=(0.85, 1.3), covlim=covlim)
    cat_ticks([axes[2 * r, 2], axes[2 * r + 1, 2]], snrs, rotation=0, labels=[f"{v:g}" for v in snrs])
    axes[2 * r, 0].set_ylabel(f"{KIND[kind].split(' (')[0]}\nwidth / M3"); axes[2 * r + 1, 0].set_ylabel("coverage")
axes[0, 0].set_title("labeled $n$ ($N=20n$)", pad=2); axes[0, 1].set_title("unlabeled $N$ ($n=100$)", pad=2)
axes[0, 2].set_title("signal-to-noise (SNR)", pad=2)
for j in range(3):
    axes[3, j].set_xlabel(("$n$", "$N$", "SNR")[j])
fig.tight_layout(rect=(0, 0.08, 1, 1), h_pad=0.5, w_pad=0.4)
finish(fig, axes, "synthetic_factors")
