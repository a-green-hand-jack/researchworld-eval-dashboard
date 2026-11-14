import os, sys
alpha = float(sys.argv[1]); os.environ["ALPHA"] = str(alpha)
sys.path.insert(0, "/work/analysis")
import pandas as pd
from e5_analysis import table
tag = "cifar10h" if alpha == 0.1 else "_a%g" % alpha
sc = ["euclid", "hellinger", "chi2", "kl", "aitchison_1e-3"]
df = table(tag, "resnet56_T", [("split", s) for s in sc] + [("mondrian_conf", "chi2")], B=100)
rows = []
for _, r in df.iterrows():
    rows.append(dict(alpha=alpha, method=r.method, score=r.score, cov=r.cov_split_mean, G_conf=r.G_conf[0], G_class=r.G_class[0], min_conf=r.min_conf[0], lm1=r.lm1[0], null_conf=r.null_conf))
pd.DataFrame(rows).to_csv(f"/work/results/e5_alpha_summary_{alpha}.csv", index=False)
