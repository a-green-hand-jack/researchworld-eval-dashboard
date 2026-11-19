import sys
import pandas as pd
from metrics import tidy
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
df = tidy(sys.argv[1])
d = df[df.method.str.endswith("_beta") == False]
for scen in sorted(d.scen.unique()):
    for col in ["mae", "spearman", "bias"]:
        t = d[d.scen == scen].pivot_table(index="method", columns="n", values=col, aggfunc="mean")
        print(scen, col); print(t.round(4)); print()
b = df[df.method.str.endswith("_beta")]
print(b.groupby(["scen", "method", "n"]).beta.mean().unstack().round(2))
