"""Render tables/*.tex from figures/gen/data.py. Usage: python3 figures/gen/make_tables.py"""
import os
from data import TASK1, VS, VS_MODEL, XJ, ZN

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "tables")


def write(name, s):
    with open(os.path.join(OUT, name), "w") as f:
        f.write(s)


def best(vals, hi=True):
    t = max(vals) if hi else min(vals)
    return [v == t for v in vals]


def cell(v, b, fmt="{:.4f}"):
    s = fmt.format(v).replace("-", "$-$")
    return r"\textbf{%s}" % s if b else s


# ---- Task 1 (table_kf): grouped by model type, bold = best per column over all rows
cols = list(zip(*[r[2:] for r in TASK1]))
bm = [best(c) for c in cols]
rows = []
for typ, label in (("LMM", r"\textit{Large multimodal models (description $\rightarrow$ text embedding)}"),
                   ("CLIP", r"\textit{Contrastive image--text encoders}")):
    rows.append(r"\multicolumn{5}{@{}l}{%s} \\" % label)
    for i, r in enumerate(TASK1):
        if r[1] != typ:
            continue
        rows.append("%s & %s \\\\" % (r[0], " & ".join(cell(r[2 + j], bm[j][i]) for j in range(4))))
    if typ == "LMM":
        rows.append(r"\midrule")
write("table_kf.tex", r"""\begin{table}[tb]
  \centering
  \caption{Task~1 (closed-set classification of dish crops, 218 classes): F1 and Recall@$K$ (fraction of crops whose true class is among the top-$K$ predictions). Rows are grouped by model type and sorted by F1 within a group; \textbf{bold} marks the best value in each column over all models. The ranking depends on the metric: the two contrastive encoders have the best R@5 but lower R@1 than GPT-4o and the three strongest open LMMs.}
  \resizebox{\columnwidth}{!}{\begin{tabular}{@{}lcccc@{}}
      \toprule
      \textbf{Model} & \textbf{F1}~$\uparrow$ & \textbf{R@1}~$\uparrow$ & \textbf{R@3}~$\uparrow$ & \textbf{R@5}~$\uparrow$ \\
      \midrule
      %s
      \bottomrule
    \end{tabular}}
  \label{table:classification_comparison}
\end{table}
""" % "\n      ".join(rows))

# ---- Task 3 (table_vs): add signed change row
hdr = ["F1", "P@1", "R@1", "R@3", "R@5"]
a, b = VS["w/o description"], VS["w/ description"]
bb = [best([a[j], b[j]]) for j in range(5)]
r1 = " & ".join(cell(a[j], bb[j][0]) for j in range(5))
r2 = " & ".join(cell(b[j], bb[j][1]) for j in range(5))
d = " & ".join(("$+$" if b[j] - a[j] > 0 else "$-$") + "{:.4f}".format(abs(b[j] - a[j])) for j in range(5))
write("table_vs.tex", r"""\begin{table}[tb]
  \centering
  \caption{Task~3 (menu-aware classification of dishes in multi-dish images) with %s: F1, Precision@1 and Recall@$K$ without and with a menu-level description of the whole image. The description raises F1 and P@1 but lowers all recall values; $\Delta$ is with minus without description. \textbf{Bold}: better of the two rows.}
  \resizebox{\columnwidth}{!}{\begin{tabular}{@{}lccccc@{}}
    \toprule
    & %s \\
    \midrule
    w/o description & %s \\
    w/ description  & %s \\
    \midrule
    $\Delta$        & %s \\
    \bottomrule
  \end{tabular}}
  \label{table:desc_guided}
\end{table}
""" % (VS_MODEL, " & ".join(r"\textbf{%s}~$\uparrow$" % h for h in hdr), r1, r2, d))

# ---- Diversity (table_xj)
def row(name, ours):
    out = []
    for k, hi in (("trace", True), ("sil", False), ("db", True), ("ch", False)):
        mine = XJ[name][k]
        other = XJ["UEC-Food 256" if name != "UEC-Food 256" else "FoodLogAthl-218"][k]
        for j in range(3):
            win = (mine[j] > other[j]) if hi else (mine[j] < other[j])
            fmt = "{:.2f}" if k in ("trace", "db", "ch") else "{:.4f}"
            out.append(cell(mine[j], win, fmt))
    return " & ".join(out)

write("table_xj.tex", r"""\begin{table*}[tb]
  \centering
  \caption{Class-distribution metrics of FoodLogAthl-218 versus UEC-Food~256, computed on features from three image encoders (CLIP, EVA-CLIP, Swin). Arrows point in the direction of larger intra-class spread and class overlap (i.e.\ a harder, less separable distribution): higher \emph{Trace} (total within-class scatter) and \emph{Davies--Bouldin}, lower \emph{Silhouette} and \emph{Calinski--Harabasz}. \textbf{Bold} marks the dataset that is more spread/overlapping under that encoder; FoodLogAthl-218 is so in all 12 cells. Values are only comparable within a column (same encoder), and the two datasets differ in class count (218 vs.\ 256).}
  \resizebox{\textwidth}{!}{\begin{tabular}{@{}lcccccccccccc@{}}
      \toprule
        & \multicolumn{3}{c}{\textbf{Trace ($\uparrow$)}}
        & \multicolumn{3}{c}{\textbf{Silhouette ($\downarrow$)}}
        & \multicolumn{3}{c}{\textbf{Davies--Bouldin ($\uparrow$)}}
        & \multicolumn{3}{c}{\textbf{Calinski--Harabasz ($\downarrow$)}} \\
      \cmidrule(lr){2-4} \cmidrule(lr){5-7} \cmidrule(lr){8-10} \cmidrule(l){11-13}
      \textbf{Dataset}
      & CLIP & EVA-CLIP & Swin
      & CLIP & EVA-CLIP & Swin
      & CLIP & EVA-CLIP & Swin
      & CLIP & EVA-CLIP & Swin \\
      \midrule
      UEC-Food 256 & %s \\
      FoodLogAthl-218 (ours) & %s \\
      \bottomrule
    \end{tabular}}
  \label{table:diversity_metrics_comparison}
\end{table*}
""" % (row("UEC-Food 256", False), row("FoodLogAthl-218", True)))

# ---- Filtering funnel (table_zn): diffs computed from the counts
def diff(i, k):
    if i == 0:
        return ""
    d = ZN[i][k] - ZN[i - 1][k]
    return "%s%s" % ("$-$" if d < 0 else ("$+$" if d > 0 else ""), "{:,}".format(abs(d))) if d else "0"

lines = []
for i, (s, op, im, bx, cl) in enumerate(ZN):
    c = []
    for k, v in ((2, im), (3, bx), (4, cl)):
        c.append("{:,}".format(v))
        c.append(diff(i, k))
    lines.append("%d & %s & %s \\\\" % (s, op, " & ".join(c)))
write("table_zn.tex", r"""\begin{table*}[tb]
  \centering
  \caption{Data filtering and curation pipeline: counts after each step, with the change from the previous step. Steps~1--2 remove log records without a usable image or bounding box, step~3 drops classes with fewer than 10 samples, step~4 flags crops more than 1.5 SD from their class centroid in CLIP ViT-B/16 feature space, step~5 is manual review (an image is removed entirely if any of its dishes is invalid, so meal composition is preserved), and step~6 consolidates synonymous labels (GPT-4o grouping followed by manual refinement). Counts are of images, dish bounding boxes (bboxes) and distinct classes.}
  \begin{tabular}{@{}cl rr rr rr@{}}
    \toprule
    Step & Operation & \multicolumn{2}{c}{\#images} & \multicolumn{2}{c}{\#bboxes} & \multicolumn{2}{c}{\#classes} \\
    & & count & $\Delta$ & count & $\Delta$ & count & $\Delta$ \\
    \midrule
    %s
    \bottomrule
  \end{tabular}
  \label{data cleaning steps table}
\end{table*}
""" % "\n    ".join(lines))

# ---- Dataset comparison (table_os): citations unchanged from the input
write("table_os.tex", r"""\begin{table*}[thb]
\centering
\caption{Food image classification datasets. \#samples is the sample count reported for each dataset; for FoodLogAthl-218 it counts dish bounding boxes (14,349 boxes in 6,925 images, since one image can hold several dishes). Web-sourced data are marked in bold.}
\begin{tabular}{@{}rllrrll@{}}
\toprule
Year & Dataset & Cuisine & \#classes & \#samples & Data source \\
\midrule
2009 & PFID~\cite{chen2009pfid} & Western & 101 & 4,545 & Fast food chains \\
2014 & UEC-Food 256~\cite{kawano2015automatic} & International & 256 & 25,088 & \textbf{Web} + original database \\
2014 & Food-101~\cite{bossard2014food} & Western & 101 & 101,000 & \textbf{Web} (foodspotting.com) \\
2015 & UPMC Food-101~\cite{wang2015recipe} & Western & 101 & 90,840 & \textbf{Web} (Google~\cite{google}) \\
2016 & UNICT-FD1200~\cite{farinella2016retrieval} & International & 1,200 & 4,754 & Experiment participants \\
2017 & Vegfru~\cite{hou2017vegfru} & Vegetables, fruits & 25/292\textsuperscript{*} & 160,000 & \textbf{Web} (Google, ImageNet~\cite{imagenet}, etc.) \\
2019 & FoodAI-756~\cite{sahoo2019foodai} & International & 152/756\textsuperscript{*} & 400,000 & \textbf{Web} (Google, Bing, etc.) \\
2021 & Food2K~\cite{min2023large} & International & 2,000 & 1,036,564 & \textbf{Web} (Meituan~\cite{meituan}) \\
2023 & Food-500 Cap~\cite{ma2023food} & International & 494 & 24,700 & \textbf{Web} (Google, Bing) \\
\midrule
2025 & FoodLogAthl-218 (ours) & International & 218 & 14,349 & Dietary management app \\
\bottomrule
\end{tabular}

\smallskip
\raggedright\footnotesize\textsuperscript{*}Hierarchically structured dataset; $n$/$m$ means $m$ classes grouped into $n$ higher-level classes.
\label{Food image dataset table}
\end{table*}
""")
print("ok")
