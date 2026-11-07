import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis_lib import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40); pd.set_option('display.max_rows', 300)
exp = sys.argv[1]
by = sys.argv[2].split(",")
ests = sys.argv[3].split(",")
vals = sys.argv[4].split(",") if len(sys.argv) > 4 else ["bias", "sd", "rmse"]
scen, df, pred = load(exp)
df = df[df["est"].isin(ests)]
S = summarize(df, by + ["est"], ci=False)
for v in vals:
    print(v)
    print(S.pivot_table(index=by, columns="est", values=v).round(3))
