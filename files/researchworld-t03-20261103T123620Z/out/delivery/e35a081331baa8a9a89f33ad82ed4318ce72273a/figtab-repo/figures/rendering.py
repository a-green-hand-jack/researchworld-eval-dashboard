"""Shared publication rendering; no numerical data or statistical inference.

This helper does not generate a result on its own. Result-specific generators
will call it once committed analysis outputs and final schemas are available.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import platform

import matplotlib as mpl

WIDTH_IN = 5.5
# Consistent method identity; redundant style survives grayscale printing.
METHOD_STYLE = {
    "permutation": {"color": "#0072B2", "marker": "o", "linestyle": "-"},
    "kernel": {"color": "#D55E00", "marker": "s", "linestyle": "--"},
}


@contextmanager
def paper_style():
    """Temporary defaults for the official single-column NeurIPS geometry."""
    with mpl.rc_context({
        "font.family": "serif", "font.serif": ["STIXGeneral"],
        "mathtext.fontset": "stix", "font.size": 9,
        "axes.titlesize": 10, "axes.labelsize": 9,
        "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5, "axes.spines.top": False,
        "axes.spines.right": False, "axes.linewidth": 0.7,
        "lines.linewidth": 1.25, "lines.markersize": 4,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.bbox": None, "figure.constrained_layout.use": True,
    }):
        yield


def file_record(path, root):
    """Hash an actual input/output using a portable repository-relative path."""
    root = Path(root).resolve()
    path = Path(path).resolve()
    relative = path.relative_to(root)
    if not path.is_file():
        raise FileNotFoundError(path)
    return {"path": relative.as_posix(), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def export_figure(fig, output_stem, *, root, inputs, analysis_revision,
                  generator, command, panels, caption_path):
    """Export PDF/inspection PNG and a provenance manifest, never fake values.

    `panels` is the result-specific mapping of panel to file/column/filter and
    statistical definitions. Statistical calculations remain analysis-owned.
    Human inspection is deliberately recorded separately after opening outputs.
    """
    if len(analysis_revision) != 40 or any(c not in "0123456789abcdef" for c in analysis_revision):
        raise ValueError("Supply the full verified analysis commit revision")
    if not inputs or not panels or not command:
        raise ValueError("Inputs, panel mappings and reproduction command are required")
    root = Path(root).resolve()
    stem = Path(output_stem).resolve()
    stem.relative_to(root)  # Refuse an untracked output location.
    records = [file_record(p, root) for p in inputs]
    generator_record = file_record(generator, root)
    caption_record = file_record(caption_path, root)
    stem.parent.mkdir(parents=True, exist_ok=True)
    pdf, png = stem.with_suffix(".pdf"), stem.with_suffix(".png")
    # Preserve figsize: bbox_inches='tight' changes the delivered physical size.
    fig.savefig(pdf, bbox_inches=None)
    fig.savefig(png, dpi=200, bbox_inches=None)
    manifest = {
        "schema_version": 1, "analysis_revision": analysis_revision,
        "inputs": records, "generator": generator_record,
        "supporting_code": [file_record(Path(__file__), root)],
        "caption": caption_record, "command": command, "panels": panels,
        "versions": {"python": platform.python_version(), "matplotlib": mpl.__version__},
        "width_inches": float(fig.get_figwidth()),
        "height_inches": float(fig.get_figheight()),
        "outputs": [file_record(p, root) for p in (pdf, png)],
        "inspection": "Pending: record visual and integrated-PDF checks separately",
    }
    stem.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest
