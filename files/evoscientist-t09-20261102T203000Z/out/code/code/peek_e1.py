import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis_lib import *
pd.set_option('display.width',250); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',200)
scen, df, pred = load("E1")
df["mech2"] = df["mech"] + np.where(df["mech"]=="pow", "-"+df["o_kappa"].astype(str), "")
S = summarize(df, ["mech2","est"], ci=False)
for v in ["bias","sd","rmse"]:
    print(v); print(S.pivot(index="est", columns="mech2", values=v).round(2))
print("valid"); print(S.pivot(index="est", columns="mech2", values="valid").round(2).loc[["Hajek-full","Hajek-eps"]])
S2 = summarize(df, ["g_kind","est"], ci=False)
print(S2.pivot(index="est", columns="g_kind", values="rmse").round(2))
