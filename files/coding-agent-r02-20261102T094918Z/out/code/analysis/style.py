import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6, "lines.linewidth": 1.3, "lines.markersize": 4,
    "grid.color": "#dddddd", "grid.linewidth": 0.5, "axes.grid": True, "axes.axisbelow": True, "pdf.fonttype": 42,
    "figure.dpi": 150, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})
COL = {"euclid": "#2a78d6", "tv": "#6250d6", "hellinger": "#1baf7a", "chi2": "#eb6834", "kl": "#c98500", "aitchison": "#e34948"}
MK = {"euclid": "o", "tv": "s", "hellinger": "^", "chi2": "D", "kl": "v", "aitchison": "P"}
LAB = {"euclid": "Euclid", "tv": "TV", "hellinger": "Hellinger", "chi2": r"Pearson $\chi^2$", "kl": "KL", "aitchison": "Aitchison"}
FIG = "/work/paper/figs/"
