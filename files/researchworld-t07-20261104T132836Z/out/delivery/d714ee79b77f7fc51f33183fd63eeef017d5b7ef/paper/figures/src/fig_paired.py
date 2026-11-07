"""C2: pre-declared headline comparison, MASS-Ens vs references, paired RMSE ratio per benchmark.  Outputs: paired_rmse_mass_ens.pdf, paired_rmse_mass.pdf (co-headline, story-repo PLAN v1.1)

Per benchmark: ratio RMSE(MASS-Ens)/RMSE(reference) = 1 + delta/RMSE_ref, where delta and its model-level (extrap) or
split-level (random) 95% paired-bootstrap CI come from the committed paired.csv and RMSE_ref is the reference's point
estimate in cells.csv (the CI is scaled by that point estimate, i.e. it ignores the reference's own sampling noise
inside the ratio; the paired difference already accounts for it).  Bottom rows: cross-benchmark geometric-mean ratio
and benchmark-level bootstrap CI (aggregate.csv; second row recomputed here, same definition, on the 9 benchmarks without
an asterisk, i.e. excluding the four development benchmarks).  Reference `best` = baseline with the lowest source-CV RMSE (best_baseline.csv).
"""
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import common as C

PROTOS = ["extrap", "random"]
REFS = [("random", "vs. Random mean"), ("ridge", "vs. Random + ridge"), ("best_cv", "vs. best source-CV")]


def build(cells, paired, best, PROP):
    c = cells[cells.metric == "rmse"].set_index(["bench", "protocol", "method", "n"])["mean"]
    p = paired[(paired.metric == "rmse") & (paired.method == PROP)].copy()
    rows = []
    for r in p.itertuples():
        ref = r.ref
        if ref not in c.index.get_level_values("method"):
            continue
        base = c.get((r.bench, r.protocol, ref, r.n))
        if base is None:
            continue
        rows.append(dict(bench=r.bench, protocol=r.protocol, n=r.n, ref=ref, ratio=1 + r.delta_mean / base,
                         lo=1 + r.ci_lo / base, hi=1 + r.ci_hi / base))
    d = pd.DataFrame(rows)
    d["refkey"] = d.ref
    if best is not None:
        bk = {(b.bench, b.protocol): b.method for b in best.itertuples()}
        mask = [bk.get((r.bench, "extrap" if r.protocol.startswith("extrap") else "random")) == r.ref for r in d.itertuples()]
        dup = d[mask].copy()
        dup["refkey"] = "best_cv"
        d = pd.concat([d, dup])
    return d


def main(PROP):
    C.style()
    cells, paired = C.load("cells.csv"), C.load("paired.csv")
    best = C.load("best_baseline.csv", required=False)
    agg = C.load("aggregate.csv", required=False)
    d = build(cells, paired, best, PROP)
    bs = C.benches(d)
    refs = [r for r in REFS if r[0] in set(d.refkey)]
    protos = [p for p in PROTOS if p in set(d.protocol)]
    fig, axes = plt.subplots(len(protos), len(refs), figsize=(C.TEXTWIDTH, 2.7 * len(protos) + 0.3), sharey=True, squeeze=False)
    ys = {b: i for i, b in enumerate(bs)}
    nagg = len(bs) + 0.8
    nnon = len(bs) + 1.8   # extra row: geometric mean over the non-development benchmarks
    for i, p in enumerate(protos):
        for j, (rk, rt) in enumerate(refs):
            ax = axes[i, j]
            for n, mk, fc, off in [(50, "o", C.color(PROP), -0.15), (100, "o", "white", 0.15)]:
                g = d[(d.protocol == p) & (d.refkey == rk) & (d.n == n)]
                for r in g.itertuples():
                    y = ys[r.bench] + off
                    ax.plot([r.lo, r.hi], [y, y], color=C.color(PROP), lw=0.9)
                    ax.plot(r.ratio, y, mk, mfc=fc, mec=C.color(PROP), ms=3, mew=0.8)
                if agg is not None:
                    a = agg[(agg.protocol == p) & (agg.metric == "rmse") & (agg.method == PROP) & (agg.ref == rk) & (agg.n == n)]
                    if len(a):
                        a = a.iloc[0]; y = nagg + off
                        ax.plot([a.ci_lo, a.ci_hi], [y, y], color="k", lw=1.2)
                        ax.plot(a.effect, y, "D", mfc=("k" if n == 50 else "white"), mec="k", ms=3.2, mew=0.9)
                g = d[(d.protocol == p) & (d.refkey == rk) & (d.n == n) & ~d.bench.isin(C.DEV)].drop_duplicates("bench")
                if len(g) >= 3:
                    gm = C.geomean_ci(g.ratio.values); y = nnon + off
                    ax.plot([gm[1], gm[2]], [y, y], color="k", lw=1.2)
                    ax.plot(gm[0], y, "s", mfc=("k" if n == 50 else "white"), mec="k", ms=3.2, mew=0.9)
            ax.axvline(1, color="k", lw=0.7)
            ax.set_xscale("log"); ax.set_xlim(0.2, 3.2); ax.set_xticks([0.25, 0.5, 1, 2]); ax.set_xticklabels(["0.25", "0.5", "1", "2"])
            ax.xaxis.set_minor_locator(plt.NullLocator())
            ax.set_ylim(nnon + 0.8, -0.8)
            ax.set_yticks(list(ys.values()) + [nagg, nnon]); ax.set_yticklabels([C.bl(b) for b in bs] + ["geo. mean, all 13", "geo. mean, 9 non-dev."], fontsize=6)
            ax.grid(axis="y", visible=False)
            if i == 0:
                ax.set_title(rt, fontsize=7)
            if j == len(refs) - 1:
                ax.text(1.03, 0.5, C.PROTO_LABEL[p].split(" (")[0], transform=ax.transAxes, rotation=270, va="center", fontsize=7.5)
    h = [plt.Line2D([], [], marker="o", color=C.color(PROP), mfc=fc, lw=0.9, ms=3, label=f"$n={n}$") for n, fc in [(50, C.color(PROP)), (100, "white")]]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.03))
    fig.supxlabel(f"RMSE of {C.ml(PROP)} / RMSE of reference  ($<1$: {C.ml(PROP)} better)", fontsize=7, y=0.06)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    C.save(fig, f"paired_rmse_{PROP}.pdf")


if __name__ == "__main__":
    for m in ("mass_ens", "mass"):
        main(m)
