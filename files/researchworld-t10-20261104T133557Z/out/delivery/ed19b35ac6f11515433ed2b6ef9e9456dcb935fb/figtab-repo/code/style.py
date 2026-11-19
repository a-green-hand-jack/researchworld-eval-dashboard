"""Shared figure style: Okabe-Ito colour-blind-safe palette, fixed colour+marker per method across all figures."""
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt

TEXT_W = 5.5   # inches; NeurIPS/ICLR/ICML text width ~5.5-6.75in -- confirm with venue-repo
METHOD_STYLE = {   # method name as in experiment-repo summarize.py -> (label, colour, marker)
    "classical": ("Classical (labeled only)", "#555555", "x"),
    "ppi": ("PPI ($\\lambda$=1)", "#E69F00", "s"),
    "ppi++": ("PPI++ (reference)", "#000000", "o"),
}
DATASET_LABEL = {"galaxies": "galaxies", "forest": "forest", "alphafold": "alphafold",
                 "gene_expression": "gene expr.", "census_income": "census income",
                 "census_healthcare": "census health", "census_education": "census educ."}

def setup():
    plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": "#dddddd", "grid.linewidth": 0.5, "axes.axisbelow": True,
        "pdf.fonttype": 42, "ps.fonttype": 42, "figure.dpi": 150, "savefig.bbox": "tight",
        "font.family": "serif"})


_CF = {"poly_f": ("cubic in $f$", "#E69F00", "h"), "lin_f": ("linear in $f$", "#56B4E9", "^"), "iso_f": ("isotonic in $f$", "#009E73", "D"),
       "gbm_f": ("GBM on $f$", "#CC79A7", "v"), "lin_fX": ("linear in $(f,X)$", "#0072B2", "P"),
       "gbm_fX": ("GBM on $(f,X)$", "#D55E00", "X")}

def style_of(method):
    """label, colour, marker for a summarize.py method name; suffix _t = t-calibrated, _boot = studentised bootstrap."""
    if method == "ppi++": return ("PPI++, Wald", "#7a7a7a", "o")
    if method in METHOD_STYLE: return METHOD_STYLE[method]
    if method == "cf_lin_f": return ("cross-fit linear in $f$", "#56B4E9", "^")
    if method == "oracle": return ("oracle $E[Y|f,X]$ (unavailable)", "#999999", "*")
    suf = ""
    for sfx, txt in (("_t", ", $t$"), ("_boot", ", boot")):
        if method.endswith(sfx): method, suf = method[: -len(sfx)], txt
    if method.startswith("cf_") and method[3:] in _CF:
        lab, c, mk = _CF[method[3:]]; return ("cross-fit " + lab + suf, c, mk)
    if method == "ppi++": return ("PPI++" + suf, {"": "#7a7a7a", ", $t$": "#000000", ", boot": "#8B0000"}[suf], "o")
    raise KeyError(method)
