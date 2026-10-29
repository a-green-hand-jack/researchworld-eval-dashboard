"""Closed-form log overshoot ln(2m(n-1) / C) of the generic bound on four families with exact cover times.

Exact start-averaged cover times (elementary derivations; H_k = k-th harmonic number, N = n-1):
  path      C = N^2 + N(N-1)/6,          m = N
  cycle     C = n(n-1)/2,                m = n
  complete  C = (n-1) H_{n-1},           m = n(n-1)/2
  star      C = 2N H_{N-1} + 1/(N+1),    m = N
Also writes the label-noise floor implied by the median relative standard error (Gaussian approximation).
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent


def H(k):
    return sum(1.0 / i for i in range(1, k + 1))


def cover(fam, n):
    N = n - 1
    if fam == "path":
        return N * N + N * (N - 1) / 6, N
    if fam == "cycle":
        return n * (n - 1) / 2, n
    if fam == "complete":
        return (n - 1) * H(n - 1), n * (n - 1) // 2
    if fam == "star":
        return 2 * N * H(N - 1) + 1.0 / (N + 1), N
    raise ValueError(fam)


FAMS = ["path", "cycle", "star", "complete"]
ns = list(range(6, 31))
gap = {f: [math.log(2 * cover(f, n)[1] * (n - 1) / cover(f, n)[0]) for n in ns] for f in FAMS}
out = {"n": ns, "log_overshoot": gap}

# @evidence[[paper_data.json#final_evaluation.metrics.mc_rel_se_median]]
se = json.loads((ROOT / "paper_data.json").read_text())["final_evaluation"]["metrics"]["mc_rel_se_median"]
macro = json.loads((ROOT / "paper_data.json").read_text())["final_evaluation"]["metrics"]["macro_log_mae"]
out["noise_floor_mae_gaussian"] = math.sqrt(2 / math.pi) * se
out["noise_floor_fraction_of_macro"] = out["noise_floor_mae_gaussian"] / macro
out["worst_case_family_mean_log_error"] = 12 * macro
out["worst_case_family_mean_factor"] = math.exp(12 * macro)
out["worst_case_graph_log_error"] = 24 * macro
out["worst_case_graph_factor"] = math.exp(24 * macro)
(ROOT / "closed_form_gap.json").write_text(json.dumps(out, indent=1) + "\n")

plt.rcParams.update({"font.size": 11, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10})
fig, ax = plt.subplots(figsize=(5.0, 3.2))
style = {"path": ("#2a9d8f", "-"), "cycle": ("#7b4fa3", "--"), "star": ("#e07b24", "-."), "complete": ("#222a35", ":")}
for f in FAMS:
    c, ls = style[f]
    ax.plot(ns, gap[f], color=c, ls=ls, lw=2.2, label=f)
ax.set_xlabel("Number of vertices $n$")
ax.set_ylabel(r"$\ln\,[\,2m(n-1)\,/\,C\,]$")
ax.legend(frameon=False, fontsize=10, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(ROOT / "figures" / "closed_form_gap.pdf")
fig.savefig(ROOT / "figures" / "closed_form_gap.png", dpi=300)
print(json.dumps({k: v for k, v in out.items() if k not in ("n", "log_overshoot")}, indent=1))
for f in FAMS:
    print(f, [round(gap[f][ns.index(n)], 3) for n in (6, 10, 20, 30)])
