"""T8 (claim E4): out-of-sample bias of the fitted line and of the parameter-free first-order prediction.

Reads s5_oos_summary.csv: for every data set, the mean of log(prediction) - log(verified budget) over its adjacent-pair claims (bias, natural
log; exp(bias) = geometric-mean ratio prediction / budget) with the claim-resampled 95% interval, for (i) the line log k = a + b log z fitted on
the NBA single seasons only (so out of sample for every other data set; in sample for the seasons) and (ii) k_hat, the first-order estimate
from s5_khat.csv, which has no fitted parameter. Also the root-mean-square error of log k and the share of claims with k_hat within a factor 2.
Writes table8_oos.tex.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common as C

A = C.args(__doc__)
o = C.read(A.results, "s5_oos_summary.csv").set_index("dataset")


def fac(b, lo, hi):
    return f"{np.exp(b):.2f} [{np.exp(lo):.2f}, {np.exp(hi):.2f}]"


rows = []
for d, lab in [("nba_seasons", "NBA single seasons (in sample)"), ("arena55k", "Arena 55k"), ("mt_human", "MT-Bench human"), ("mt_gpt4", "MT-Bench GPT-4"),
               ("nba_all", "NBA all seasons")]:
    r = o.loc[d]
    rows.append(" & ".join([lab, f"{int(r.n_claims)}", fac(r.bias_logk_z, r.bias_z_lo, r.bias_z_hi), f"{r.rmse_logk_z:.2f}",
                            fac(r.bias_logk_khat, r.bias_khat_lo, r.bias_khat_hi), f"{r.rmse_logk_khat:.2f}", f"{100 * r.share_khat_within_2x:.0f}\\%"]) + r" \\")
tex = "\n".join([r"\begin{tabular}{lrcrcrr}", r"\toprule",
                 r" & & \multicolumn{2}{c}{NBA-seasons line} & \multicolumn{2}{c}{first-order $\hat k$} & \\",
                 r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}",
                 r"Data & Claims & predicted / verified $k$ & RMSE($\log k$) & predicted / verified $k$ & RMSE($\log k$) & $\hat k$ within $2\times$ \\", r"\midrule",
                 *rows, r"\bottomrule", r"\end{tabular}", ""])
open(os.path.join(A.out, "table8_oos.tex"), "w").write(tex)
C.record_inputs(A.out, "table8_oos.tex", [os.path.join(A.results, "s5_oos_summary.csv")])
