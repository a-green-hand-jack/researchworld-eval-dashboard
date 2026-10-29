"""Shared figure style: NeurIPS 2026 single column (text width 5.5 in, Times-like 10 pt body, >=7 pt text)."""
import matplotlib as mpl
TEXTW = 5.5  # inches; two panels side by side: 2.7 in each
# Okabe-Ito colour-blind-safe palette; series also differ by marker and linestyle
DATASETS = {  # key -> (label, colour, marker, linestyle)
    "arena55k": ("Arena 55k (crowd)", "#0072B2", "o", "-"),
    "mtbench_human": ("MT-Bench (expert)", "#D55E00", "s", "--"),
    "mtbench_gpt4": ("MT-Bench (GPT-4 judge)", "#009E73", "^", "-."),
    "nba": ("NBA (sports)", "#CC79A7", "D", ":"),
}
def apply():
    mpl.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "legend.frameon": False,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
        "lines.linewidth": 1.2, "lines.markersize": 4, "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "figure.dpi": 150,
    })
