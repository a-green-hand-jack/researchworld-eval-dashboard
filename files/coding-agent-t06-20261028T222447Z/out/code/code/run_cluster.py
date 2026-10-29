"""Sensitivity to the iid assumption: question-clustered bootstrap for MT-Bench and prompt-clustered bootstrap for
Arena-55k (rows sharing an identical prompt string form a cluster) vs. the model-based SE of the gap."""
import numpy as np, pandas as pd, sys
import bt, loaders as D
rng = np.random.default_rng(20261029)
rows = []
def run(name, d, cl, B=300):
    P = bt.Problem(d); th = P.fit(); p = P.p
    order = np.argsort(-th[:p])
    uniq, inv = np.unique(cl, return_inverse=True)
    idx_by = [np.where(inv == g)[0] for g in range(len(uniq))]
    ths = []
    for _ in range(B):
        pick = rng.integers(0, len(uniq), len(uniq))
        ii = np.concatenate([idx_by[g] for g in pick])
        dd = dict(items=d["items"], a=d["a"][ii], b=d["b"][ii], h=d["h"][ii], y=d["y"][ii])
        Pb = bt.Problem(dd)
        if Pb.C != P.C or Pb.L != P.L:   # cell structure changed: map through counts
            N = np.zeros_like(P.N0)
            key0 = {(P.ca[c], P.cb[c], P.ch[c]): c for c in range(P.C)}
            for c in range(Pb.C):
                N[key0[(Pb.ca[c], Pb.cb[c], Pb.ch[c])]] += Pb.N0[c]
        else:
            N = Pb.N0
        ths.append(P.fit(N, th)[:p])
    ths = np.array(ths)
    # iid bootstrap for reference
    iid = np.array([P.fit(P.resample_counts(rng), th)[:p] for _ in range(B)])
    for r in range(p - 1):
        i, j = order[r], order[r + 1]
        g = th[i] - th[j]
        rows.append(dict(board=name, rank=r + 1, gap=g, se_model=P.gap_se(th, i, j), sd_iid=float((iid[:, i] - iid[:, j]).std(ddof=1)),
                         sd_cluster=float((ths[:, i] - ths[:, j]).std(ddof=1)), n_clusters=len(uniq)))
import pandas as pd
mt = D.mtbench("human"); run("mt_human", mt, mt["qid"])
mg = D.mtbench("gpt4"); run("mt_gpt4", mg, mg["qid"])
# Arena-55k: cluster by identical prompt
df = pd.read_csv("/work/data/arena55k/train.csv", usecols=["prompt"])
a = D.arena55k(); assert len(df) == len(a["a"])
cl = df.prompt.values
print("arena55k: rows", len(cl), "unique prompts", len(set(cl)), "rows in a repeated prompt", int(pd.Series(cl).duplicated(keep=False).sum()))
run("arena55k", a, cl, B=200)
out = pd.DataFrame(rows); out["ratio_cluster_over_model"] = out.sd_cluster / out.se_model
out.to_csv("/work/results/cluster_check.csv", index=False)
print(out.groupby("board").agg(ratio_med=("ratio_cluster_over_model", "median"), ratio_min=("ratio_cluster_over_model", "min"), ratio_max=("ratio_cluster_over_model", "max"),
      iid_over_model=("sd_iid", "median")).round(3))
print(out.groupby("board").apply(lambda g: pd.Series(dict(n_z2_model=(g.gap / g.se_model > 2).sum(), n_z2_cluster=(g.gap / g.sd_cluster > 2).sum()))))
