"""Ad-hoc statistics quoted in the paper text that are not in a table. Output: results/extra_stats.log"""
import numpy as np
import pandas as pd
from analysis_lib import *

pd.set_option("display.width", 200)
# --- DM vs regression SD ratio (E1, iid baselines, nscale + dscale)
reps, gr, cf = load("E1")
m = metrics(reps, cf, boot=False)
pv = m.pivot_table(index="cid", columns="est", values="sd_pop")
x = pd.DataFrame(dict(r=pv.lin_frac / pv.dm)).join(cf.set_index("cid")[["tag", "gkind", "comm_sd"]])
x = x[x.tag.isin(["nscale", "dscale"]) & (x.comm_sd == 0)]
print("SD(lin_frac)/SD(dm), iid baselines: min %.2f median %.2f max %.2f" % (x.r.min(), x.r.median(), x.r.max()))
print("DM relative bias over E1 configs: mean %.4f sd %.4f" % (m[m.est == "dm"].rel_bias.mean(), m[m.est == "dm"].rel_bias.std()))
# --- harmonic vs mean-degree law (iid baselines)
v = pd.read_csv(os.path.join(TAB, "E1_varlaw.csv"))
for gk in ["er", "ba", "ws", "sbm"]:
    g = v[(v.gkind == gk) & (v.comm_sd == 0) & (v.tag != "real")]
    print(gk, "mean ratio harmonic %.3f  mean-degree %.3f" % (g.ratio.mean(), g.ratio_meandeg.mean()))
# --- E2
m2 = pd.read_csv(os.path.join(TAB, "E2_metrics.csv"))
g2 = m2[(m2.tag == "grid") & (m2.est == "lin_frac")]
print("E2 grid settings:", len(g2), " mean|bias_pred-bias| %.4f max %.4f" % ((g2.bias_pred - g2.bias).abs().mean(), (g2.bias_pred - g2.bias).abs().max()))
print("prediction inside bootstrap CI: %.3f" % ((g2.bias_pred >= g2.bias_lo) & (g2.bias_pred <= g2.bias_hi)).mean())
print("share of grid settings with bias^2 > var (n=8000): %.2f" % (g2.bias ** 2 > g2.sd ** 2).mean())
a = m2[m2.est == "lin_frac"]
print("corr(pred, obs) all settings: %.4f" % np.corrcoef(a.bias_pred, a.bias)[0, 1])
r = m2[(m2.tag == "nfloor") & (m2.est == "lin_frac") & (m2.n_spec == 8000)].iloc[0]
print("n* where bias^2 = var at s=8,p=.5,d=10: %.0f" % (8000 * r.sd ** 2 / r.bias ** 2))
print(m2[m2.tag == "nfloor"][["est", "n_spec", "bias", "sd", "rmse", "rmse_lo", "rmse_hi"]].round(3).to_string())
# --- number of simulated experiments
tot = 0
for e in ["E1", "E2", "E3", "E5", "E6", "E7"]:
    rr = pd.read_csv(os.path.join(RES, f"{e}_reps.csv.gz"), usecols=["cid", "pop", "rep"])
    n = len(rr.drop_duplicates())
    tot += n
    print(e, "simulated assignments:", n)
print("total assignments:", tot)
