"""E6: CI coverage of HC1 / 2-hop HAC / model-based SEs."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analysis_lib import *

reps, gr, cf = load("E6")
m = metrics(reps, cf, boot=False)
m["graph"] = m.tag.str.replace("cov_", "")
m["bias_over_sd"] = m.bias / m.sd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
cols = ["graph", "dkind", "s", "est", "bias", "sd", "sd_pop", "bias_over_sd", "se_hc", "se_hac", "se_mb", "cov_hc", "cov_hac", "cov_mb", "covps_hc", "covps_hac", "covps_mb"]
t = m[cols].sort_values(["graph", "dkind", "s", "est"])
print(t.round(3).to_string())
t.to_csv(os.path.join(TAB, "E6_coverage.csv"), index=False)
