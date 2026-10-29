"""Clean design contrast: MT-Bench human experts vs GPT-4 judge on the SAME items (question_id, turn, model pair).
Restrict both judgement sets to the shared items; compare the BT leaderboards and worst-case budgets. Because the human set
has several judgements per item, a one-judgement-per-item variant (random judge per item, R draws) equalises N.
Usage: 07_mtbench_contrast.py R -> results/mtbench_contrast.csv"""
import sys, numpy as np, pandas as pd, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsens
R = int(sys.argv[1]); res = os.path.dirname(os.path.abspath(__file__)) + "/../results/"
cols = ["question_id", "turn", "model_a", "model_b", "winner"]
h = pd.read_parquet(f"{rsens.DATA}/mtbench_human.parquet", columns=cols); g = pd.read_parquet(f"{rsens.DATA}/mtbench_gpt4pair.parquet", columns=cols)
def key(d):  # canonical orientation: sorted model names
    sw = d.model_a > d.model_b; a = np.where(sw, d.model_b, d.model_a); b = np.where(sw, d.model_a, d.model_b)
    w = d.winner.astype(str); y = np.where(w == "model_a", 1., np.where(w == "model_b", 0., .5)); y = np.where(sw, 1 - y, y)
    return d.assign(ma=a, mb=b, y=y, key=d.question_id.astype(str) + "|" + d.turn.astype(str) + "|" + a + "|" + b)
h, g = key(h), key(g); shared = set(h.key) & set(g.key)
h, g = h[h.key.isin(shared)], g[g.key.isin(shared)].drop_duplicates("key")
def comp(d, name): 
    names = sorted(set(d.ma) | set(d.mb)); ix = {n: i for i, n in enumerate(names)}
    return rsens.Comp(names, d.ma.map(ix), d.mb.map(ix), d.y, name)
def budgets(c):
    th = rsens.fit(c); r = rsens.ranking(th, c.p); o = {"N": c.n, "n_items": len(shared), "top1": c.names[r[0]], "ranking": ">".join(c.names[i] for i in r)}
    q = rsens.qvec(c, r[0], r[1]); o["z_top"] = (th[r[0]] - th[r[1]]) / np.sqrt(q @ np.linalg.inv(rsens.hess(c, th)) @ q)
    for m in ("drop", "flip"):
        o[f"top1_{m}"] = min(rsens.worst_case(c, r[0], r[j], m, th0=th)["k"] for j in (1, 2, 3))
        o[f"adjmin_{m}"] = min(rsens.worst_case(c, r[i], r[i + 1], m, th0=th)["k"] for i in range(c.p - 1))
    return o
rows = [dict(source="gpt4", rep=-1, **budgets(comp(g, "gpt4_shared"))), dict(source="human_all_judgements", rep=-1, **budgets(comp(h, "human_shared")))]
rng = np.random.default_rng(3)
for i in range(R):
    one = h.sample(frac=1, random_state=int(rng.integers(1e9))).drop_duplicates("key")
    rows.append(dict(source="human_one_per_item", rep=i, **budgets(comp(one, "human_one"))))
    bs = g.sample(frac=1, replace=True, random_state=int(rng.integers(1e9)))
    rows.append(dict(source="gpt4_bootstrap", rep=i, **budgets(comp(bs, "gpt4_bs"))))
pd.DataFrame(rows).to_csv(res + "mtbench_contrast.csv", index=False)
print(pd.DataFrame(rows).groupby("source")[["N", "z_top", "top1_drop", "top1_flip", "adjmin_drop", "adjmin_flip"]].mean())
