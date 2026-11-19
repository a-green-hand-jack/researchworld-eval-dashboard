"""H4 / C5: observed-graph error q x interference range (grid e11). Reads results/summary/e11.csv; writes
  c11_map.csv   per estimator x q x range (w2) x response: median and max over the four graphs of the normalised bias, sd and RMSE
                (RMSE/(|beta|+|gamma|)); `bias_pred` is the exact projection bias given the perturbed features
  c11_check.csv measured vs exact predicted bias per cell (REG-L, Q, G; the oracle form REG-O has no projection bias to compare when features are exact)."""
import numpy as np
import pandas as pd

s = pd.read_csv("results/summary/e11.csv")
s["graph"] = s["graph.kind"]; s["q"] = s["obs.q"]; s["range"] = np.where(s["out.w2"] > 0, "1+2-hop", "1-hop"); s["resp"] = s["tag"]
s["abs_bias_norm"] = s.bias_norm.abs(); s["sd_norm"] = s.sd / s.scale
s["bias_pred_norm"] = s.bias_pred / s.scale
rows = []
for (est, q, rg, resp), g in s.groupby(["est", "q", "range", "resp"]):
    rows.append(dict(est=est, q=q, range=rg, resp=resp, n_graphs=len(g), abs_bias_median=g.abs_bias_norm.median(), abs_bias_max=g.abs_bias_norm.max(),
                     sd_median=g.sd_norm.median(), rmse_median=g.rmse_norm.median(), rmse_max=g.rmse_norm.max(), rmse_lo_median=g.rmse_norm_lo.median(),
                     rmse_hi_median=g.rmse_norm_hi.median()))
m = pd.DataFrame(rows)
m.to_csv("results/summary/c11_map.csv", index=False)
z = (s.bias - s.bias_pred) / np.sqrt(s.bias_se ** 2 + s.bias_pred_se ** 2)
ck = s.assign(z=z)[["graph", "resp", "range", "q", "est", "bias", "bias_pred", "bias_se", "bias_pred_se", "z"]]
ck.to_csv("results/summary/c11_check.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
for est in ["REG-L", "REG-Q", "REG-G", "REG-O"]:
    print(est, "median over graphs of normalised RMSE (bias share in brackets omitted); rows q, columns range/response")
    print(m[m.est == est].pivot(index="q", columns=["range", "resp"], values="rmse_median").round(3))
print("median |bias_norm| REG-L"); print(m[m.est == "REG-L"].pivot(index="q", columns=["range", "resp"], values="abs_bias_median").round(3))
print("sd REG-L"); print(m[m.est == "REG-L"].pivot(index="q", columns=["range", "resp"], values="sd_median").round(3))
k = ck[ck.est != "REG-O"]
print("measured vs predicted: corr", np.corrcoef(k.bias, k.bias_pred)[0, 1], "median |diff|", (k.bias - k.bias_pred).abs().median(), "max", (k.bias - k.bias_pred).abs().max(), "frac |z|>2", (k.z.abs() > 2).mean())
print("DM rmse_norm median", s[s.est == "DM"].rmse_norm.median() if (s.est == "DM").any() else "n/a")
