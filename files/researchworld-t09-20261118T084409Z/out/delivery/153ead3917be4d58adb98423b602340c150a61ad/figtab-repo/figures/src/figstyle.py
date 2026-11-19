"""Shared figure style. Venue numbers live in VENUE; set them from venue-repo's page.

Widths are inches at the size the figure is placed (no LaTeX rescaling), so the
type size printed is the type size set here.
"""
import os
import matplotlib as mpl
import matplotlib.pyplot as plt

# NeurIPS 2026 (venue-repo docs/venue.md): text block 5.5 in, one column; two
# side-by-side panels ~2.7 in each; printed text >= 7 pt, aim 8 pt.
VENUE = {"name": "NeurIPS 2026", "col_in": 2.7, "text_in": 5.5, "min_pt": 7.0}

# Okabe-Ito: distinguishable under colour-vision deficiency; every series also
# gets a marker and a line style so greyscale prints still separate them.
COLORS = {"reg": "#0072B2", "reg_o": "#56B4E9", "ht": "#D55E00", "dm": "#000000",
          "flex": "#009E73", "stag": "#CC79A7", "gcr": "#E69F00"}
MARKERS = {"reg": "o", "reg_o": "s", "ht": "^", "dm": "x", "flex": "D", "stag": "P", "gcr": "v"}
LINES = {"reg": "-", "reg_o": "--", "ht": "-.", "dm": ":", "flex": "-", "stag": "--", "gcr": "-."}
FAMILY_COLORS = {"ER": "#0072B2", "SBM": "#56B4E9", "BA": "#D55E00", "WS": "#009E73", "Stanford3": "#CC79A7", "ego-Facebook": "#E69F00"}
FAMILY_KEYS = {"er": "ER", "sbm": "SBM", "ba": "BA", "ws": "WS", "stanford3": "Stanford3", "egofb": "ego-Facebook"}
FAMILY_MARKERS = {"ER": "o", "SBM": "s", "BA": "^", "WS": "D", "Stanford3": "P", "ego-Facebook": "X"}


def apply(min_pt=None):
    pt = max(min_pt or 8.0, VENUE["min_pt"])  # aim 8 pt; never below the floor
    mpl.rcParams.update({
        "font.family": "serif", "font.size": pt, "axes.labelsize": pt,
        "axes.titlesize": pt, "xtick.labelsize": pt, "ytick.labelsize": pt,
        "legend.fontsize": pt, "legend.frameon": False,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.6, "lines.linewidth": 1.2, "lines.markersize": 3.5,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": "standard", "figure.dpi": 150,
        "text.usetex": False, "mathtext.fontset": "cm",
    })


def fig(width="text", aspect=0.72, **kw):
    """width: 'half' | 'text' | inches. Returns (fig, axes) at final size."""
    w = {"half": VENUE["col_in"], "text": VENUE["text_in"]}.get(width, width)
    return plt.subplots(figsize=(w, w * aspect), constrained_layout=True, **kw)


def save(fig_, path):
    """Save at exactly the drawn size (no tight bbox), so the PDF is as wide as it is placed
    and the type size printed is the type size set; report size, aspect and smallest text."""
    fig_.savefig(path)
    w, h = fig_.get_size_inches()
    print(f"{os.path.basename(path)}: {w:.2f} x {h:.2f} in, aspect {h / w:.3f}, min font pt {min_font_pt(fig_)}")


def ci_band(ax, x, y, lo, hi, key, label=None):
    ax.fill_between(x, lo, hi, color=COLORS[key], alpha=0.18, linewidth=0)
    ax.plot(x, y, color=COLORS[key], ls=LINES[key], marker=MARKERS[key], label=label)


def min_font_pt(fig_):
    """Smallest text size in a drawn figure, for the type-size check."""
    sizes = [t.get_fontsize() for t in fig_.findobj(mpl.text.Text) if t.get_text().strip()]
    return min(sizes) if sizes else None
