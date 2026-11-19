"""Distribution shift (C4): plankton, labeled 2013 / unlabeled 2014 (tag shift; truth = mean of 2014 labels) against the
within-2013 control (tag control; both sets from 2013, truth = mean of 2013 labels), same n and N = 20n.
Input: summary_final_shift.csv."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatter
from common import *
from panels import *

setup()
df = summary("shift")
M3 = "ppipp_pkg"
M = ["classical", "ppi", M3, "ppipp_nc", M4]
fig, axes = plt.subplots(2, 2, figsize=(TEXT_W, 3.3), sharex=True, sharey="row")
ns = sorted(df["n"].unique())
for j, (tag, title) in enumerate((("control", "no shift: labeled and unlabeled from 2013"),
                                  ("shift", "shift: labeled 2013, unlabeled 2014"))):
    d = df[df["tag"] == tag]
    cov_panel(axes[0, j], d, M, band=True)
    for k, m in enumerate(M):
        s = d[d["method"] == m].sort_values("n")
        axes[1, j].plot(jit(s["n"], k, len(M)), s["width_mean"], **{a: b for a, b in kw(m).items() if a != "label"})
    axes[0, j].set_title(title, pad=2)
    axes[0, j].set_ylim(0, 1.02)
    axes[1, j].set_yscale("log")
    axes[1, j].yaxis.set_minor_formatter(LogFormatter(minor_thresholds=(2, 0.5)))
    axes[1, j].set_xlabel("labeled $n$ ($N=20n$)")
cat_ticks(axes, ns, rotation=0)
axes[0, 0].set_ylabel("coverage"); axes[1, 0].set_ylabel("mean width")
h, l = axes[0, 0].get_legend_handles_labels()
fig.tight_layout(rect=(0, 0.11, 1, 1), h_pad=0.5, w_pad=0.4)
fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.01), columnspacing=1.0)
save(fig, "plankton_shift")
plt.close(fig)
