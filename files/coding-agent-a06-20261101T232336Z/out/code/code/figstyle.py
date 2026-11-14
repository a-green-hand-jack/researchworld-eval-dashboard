import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
OI = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]   # Okabe-Ito, fixed order
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
                     "lines.linewidth": 1.4, "lines.markersize": 4, "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42})
