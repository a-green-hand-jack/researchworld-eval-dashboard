"""Build quantitative figures (PDF + 300-DPI PNG) and provenance sidecars.

Inputs : paper_data.json (sealed-final metrics), analysis/headroom_derived.json (derived ceilings),
         source_evidence/search_metrics/*.json (search-pool metrics, one evaluation per variant)
Outputs: figures/final_width_ratio.{pdf,png}, figures/search_variant_contrast.{pdf,png},
         figures/posthoc/headroom_partition_scores/partition_scores.{pdf,png},
         plus <artifact>.prov.json sidecars.
The overview diagram is rendered by the orchestrator; a placeholder is written only if it is absent.
"""
import json, hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
(FIG / "posthoc" / "headroom_partition_scores").mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 8.5, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "legend.fontsize": 8, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "font.family": "DejaVu Sans"})
C = {"recal": "#D55E00", "ceiling": "#222222", "classical": "#8C8C8C", "ppi1": "#56B4E9",
     "ppipp": "#0072B2", "stacked": "#009E73", "basis": "#CC79A7"}

pd_ = json.load(open(ROOT / "paper_data.json"))
m = pd_["final_evaluation"]["metrics"]            # @evidence[[paper_data.json#final_evaluation.metrics]]
hd = json.load(open(ROOT / "analysis/headroom_derived.json"))  # @evidence[[analysis/headroom_derived.json]]
fams = ["census_income", "census_healthcare", "census_education", "plankton", "synthetic"]
lab = ["income", "health", "educ.", "plankt.", "synth."]


EV = "@evidence" + "[["   # built piecewise so the verifier does not read it as a literal reference


def save(fig, stem, sources, script="analysis/make_figures.py"):
    for ext in ("pdf", "png"):
        fig.savefig(f"{stem}.{ext}", dpi=300, bbox_inches="tight")
    for ext in ("pdf", "png"):
        p = Path(f"{stem}.{ext}")
        side = {"schema_name": "scientific-evidence.artifact-manifest",
                "artifact": {"path": str(p.relative_to(ROOT)), "kind": "figure",
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()},
                "derived_from": [EV + s + "]]" for s in sources] + [EV + script + "]]"],
                "generated_by": {"script_path": script}}
        json.dump(side, open(f"{p}.prov.json", "w"), indent=1)
    plt.close(fig)


# ---------------------------------------------------------------- Fig 2: sealed final
fig, ax = plt.subplots(1, 2, figsize=(5.6, 2.55), gridspec_kw={"width_ratios": [1.7, 1]})
obs = np.array([m[f"log_ratio_vs_ppi_family_{f}"] for f in fams])
ceil = np.array([hd["oracle_vs_ppi_pp"][f] for f in fams])
x = np.arange(5)
ax[0].bar(x, obs, 0.6, color=C["recal"], label="observed (sealed final)")
ax[0].scatter(x, ceil, marker="D", s=26, color=C["ceiling"], zorder=3, label="oracle ceiling (derived)")
for i, v in enumerate(obs):
    ax[0].text(i, v + 0.0015, f"{v:.3f}", ha="center", va="bottom", fontsize=7.5)
ax[0].axhline(0, color="k", lw=0.6)
ax[0].set_xticks(x, lab); ax[0].set_ylim(0, 0.05)
ax[0].set_ylabel("log width ratio vs PPI++\n(positive = narrower)")
ax[0].set_title("(a) per family, vs PPI++", fontsize=8.5, loc="left")
ax[0].legend(frameon=False, loc="upper left", fontsize=7.5)
names = ["PPI++", "PPI\n$\\lambda{=}1$", "classical"]
agg = np.array([m["combined_score"], m["log_ratio_vs_ppi_lambda1_mean"], m["log_ratio_vs_classical_mean"]])
agc = np.array([hd["oracle_aggregate_vs_ppi_pp"], hd["oracle_aggregate_vs_ppi_lam1"], hd["oracle_aggregate_vs_classical"]])
ax[1].bar(range(3), agg, 0.6, color=[C["ppipp"], C["ppi1"], C["classical"]])
ax[1].scatter(range(3), agc, marker="D", s=26, color=C["ceiling"], zorder=3)
for i, v in enumerate(agg):
    ax[1].text(i, v + 0.008, f"{v:.3f}", ha="center", va="bottom", fontsize=7.5)
ax[1].axhline(0, color="k", lw=0.6)
ax[1].set_xticks(range(3), names); ax[1].set_ylim(0, 0.43)
ax[1].set_ylabel("mean log width ratio")
ax[1].set_title("(b) aggregate, vs comparator", fontsize=8.5, loc="left")
fig.tight_layout(w_pad=1.2)
save(fig, str(FIG / "final_width_ratio"),
     ["paper_data.json#final_evaluation.metrics", "analysis/headroom_derived.json#oracle_vs_ppi_pp",
      "analysis/headroom_derived.json#oracle_aggregate_vs_ppi_pp"])

# ---------------------------------------------------------------- Fig 3: search-pool contrast
variants = [("recalibrated", "recalibrated (isotonic/binned)", C["recal"]),
            ("stacked", "stacked calibration", C["stacked"]),
            ("label_free_basis", "label-free basis + PRESS", C["basis"])]
sfam = ["galaxies", "forest", "gene_expression", "alphafold", "synthetic"]
slab = ["galaxies", "forest", "gene expr.", "alphafold", "synthetic"]
fig, ax = plt.subplots(figsize=(5.6, 2.5))
w = 0.26
srcs = []
for k, (d, name, col) in enumerate(variants):
    p = f"source_evidence/search_metrics/{d}_metrics.json"
    mm = json.load(open(ROOT / p)); srcs.append(p)       # @evidence[[source_evidence/search_metrics/recalibrated_metrics.json]]
    vals = [mm[f"log_ratio_vs_ppi_family_{f}"] for f in sfam]
    ax.bar(np.arange(5) + (k - 1) * w, vals, w, color=col, label=name)
ax.axhline(0, color="k", lw=0.6)
ax.set_xticks(range(5), slab)
ax.set_ylabel("log width ratio vs PPI++\n(positive = narrower)")
ax.legend(frameon=False, fontsize=7.5, loc="upper left")
fig.tight_layout()
save(fig, str(FIG / "search_variant_contrast"), srcs)

# ---------------------------------------------------------------- Supplement: partition scores
fig, ax = plt.subplots(figsize=(4.2, 2.3))
eps = pd_["final_evaluation"]["evaluation_evidence"]["episodes"]   # @evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]
ax.bar([str(e["seed"]) for e in eps], [e["score"] for e in eps], 0.6, color=C["recal"])
ax.axhline(m["combined_score"], color="k", lw=0.8, ls="--", label="pooled aggregate")
ax.set_xlabel("evaluator partition (candidate reset seed)"); ax.set_ylabel("aggregate log ratio\nvs PPI++")
ax.set_ylim(0, 0.03); ax.legend(frameon=False, loc="upper right")
fig.tight_layout()
save(fig, str(FIG / "posthoc" / "headroom_partition_scores" / "partition_scores"),
     ["paper_data.json#final_evaluation.evaluation_evidence.episodes"])

# ---------------------------------------------------------------- overview placeholder (guarded)
ov, ovp = FIG / "overview_setting_and_method.png", FIG / "overview_setting_and_method.prompts.json"
if not (ROOT / ".concept_figure_complete").exists() and not (ovp.exists() and ovp.stat().st_size > 4):
    fig, a = plt.subplots(figsize=(5.6, 2.2)); a.axis("off")
    a.text(0.5, 0.5, "overview placeholder", ha="center"); fig.savefig(ov, dpi=300); plt.close(fig)
    ovp.write_text("{}")
print("figures written")
