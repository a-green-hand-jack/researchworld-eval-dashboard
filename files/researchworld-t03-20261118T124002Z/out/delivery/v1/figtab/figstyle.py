"""Shared figure style. Venue numbers are set once here (from venue-repo's answer) and
every generator draws at the width the template places the figure at."""
import matplotlib as mpl

# From venue-repo (figtab-repo#4): ICML 2027, two-column. Inches, placed width.
VENUE = "ICML 2027"
WIDTHS = {"column": 3.25, "text": 6.75}   # figure / figure*
MIN_PT = 7                                 # smallest figure text at placed width, pt
CAPTION_PT = 9                             # captions are set by the template, not in the figure

# Okabe-Ito: colour-blind safe; fixed assignment per explainer arm (colour follows the entity).
ARM_COLOR = {
    "default": "#D55E00",
    "l1off_paired": "#0072B2",
    "permutation": "#009E73",
    "covert_lee": "#CC79A7",
}
ARM_LABEL = {
    "default": "KernelSHAP (shipped default)",
    "l1off_paired": "KernelSHAP, l1_reg=False, paired",
    "permutation": "Permutation",
    "covert_lee": "Covert–Lee unbiased",
}
# result-file arm names -> the same entities (colour follows the entity)
_R2L = {"kshap_default": "default", "kshap_l1off": "l1off_paired", "perm": "permutation", "covert_lee": "covert_lee"}
ARM_COLOR_R = {r: ARM_COLOR[l] for r, l in _R2L.items()}
ARM_LABEL_R = {r: ARM_LABEL[l] for r, l in _R2L.items()}
ARM_MARKER = {"default": "o", "l1off_paired": "s", "permutation": "^", "covert_lee": "D"}

ARM_MARKER_R = {r: ARM_MARKER[l] for r, l in _R2L.items()}


def apply(width_key="column", height_ratio=0.62):
    # mathtext shrinks sub/superscripts to 70% (4.9 pt at 7 pt); keep them at the figure's smallest size instead
    import matplotlib._mathtext as _mt
    _mt.SHRINK_FACTOR = 1.0
    assert MIN_PT and WIDTHS[width_key], "venue sizes not set in figstyle.py"
    w = WIDTHS[width_key]
    mpl.rcParams.update({
        "figure.figsize": (w, w * height_ratio),
        "font.size": MIN_PT, "axes.labelsize": MIN_PT, "axes.titlesize": MIN_PT,
        "xtick.labelsize": MIN_PT, "ytick.labelsize": MIN_PT, "legend.fontsize": MIN_PT,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.6, "lines.linewidth": 1.2, "grid.linewidth": 0.5,
        "grid.alpha": 0.4, "pdf.fonttype": 42, "savefig.bbox": "standard",
    })
