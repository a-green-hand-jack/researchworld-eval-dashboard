"""Q4: same comparisons, different labeller.

(A) MT-Bench: human expert judgments vs GPT-4 pairwise judgments on the same (question, turn, model pair) keys.
(The Arena-vs-LLM-judge comparison of the first draft was cut by plan v2: the judge data has no declared licence.)
Writes results/s2_matched_{budgets,scores,agreement}.csv.
Usage: python code/s2_matched.py [--human-draws 20]"""
import argparse
import os

import numpy as np
import pandas as pd

from btlib import analysis as an, core, data, prov, report, units

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
ELO = 400 / np.log(10)


def kendall(x, y):
    iu = np.triu_indices(len(x), 1)
    dx, dy = x[iu[0]] - x[iu[1]], y[iu[0]] - y[iu[1]]
    return float((np.sum(dx * dy > 0) - np.sum(dx * dy < 0)) / len(dx))


def mt_matched(draws, B):
    h = data.load_mt("human")
    g = data.load_mt("gpt4")
    kh, kg = pd.Series(h.key), pd.Series(g.key)
    common = sorted(set(kh) & set(kg))
    print("matched keys:", len(common), "of human", kh.nunique(), "gpt4", kg.nunique())
    mh = kh.isin(common).values
    mg = kg.isin(common).values
    variants = []
    # all human judgments on matched keys vs GPT-4 on matched keys
    variants.append(("mt_human_matched_all", "expert", h.subset(mh)))
    variants.append(("mt_gpt4_matched", "llm_judge", g.subset(mg)))
    # robustness: only keys whose (model_a, model_b) presentation order is the same in both files (the plan's 1,232 keys)
    oh = pd.Series([f"{q}|{t}|{h.names[a]}|{h.names[b]}" for q, t, a, b in zip(h.question, h.turn, h.i, h.j)])
    og = pd.Series([f"{q}|{t}|{g.names[a]}|{g.names[b]}" for q, t, a, b in zip(g.question, g.turn, g.i, g.j)])
    ord_common = set(oh) & set(og)
    print("order-matched keys:", len(ord_common))
    variants.append(("mt_human_ordmatched", "expert", h.subset(oh.isin(ord_common).values)))
    variants.append(("mt_gpt4_ordmatched", "llm_judge", g.subset(og.isin(ord_common).values)))
    # one random human judgment per key (equal N)
    hs = []
    for d in range(draws):
        rng = np.random.default_rng([7, d])
        idx = pd.Series(np.arange(len(h)))[mh]
        pick = idx.groupby(kh[mh].values).apply(lambda s: rng.choice(s.values)).values
        hs.append(h.subset(np.isin(np.arange(len(h)), pick), name=f"mt_human_matched_1per_key_d{d}"))
    rows, sc, agree = [], [], []
    for name, design, ds in variants + [(d.name, "expert", d) for d in hs]:
        u = units.mt_unit("human" if design == "expert" else "gpt4", ds=ds, name=name)[0]
        t = report.adv_table(u, heur=False, rand=False, oneshot=False, boot=B)
        t.insert(0, "variant", name)
        t.insert(1, "claim_set", "standard")
        rows.append(t)
        tp = report.adv_table(u, heur=False, rand=False, oneshot=False, raw=False, boot=B, pairs=an.all_pairs(u))
        tp.insert(0, "variant", name)
        tp.insert(1, "claim_set", "all_pairs")
        rows.append(tp)
        th = u.x0[: u.c.K]
        for k, nme in enumerate(u.c.names):
            sc.append(dict(variant=name, participant=nme, score_elo=th[k] * ELO))
    # label agreement on matched keys (human majority vs GPT-4)
    hh = pd.DataFrame(dict(key=h.key[mh], a=np.array(h.names)[h.i[mh]], b=np.array(h.names)[h.j[mh]], y=h.y[mh]))
    gg = pd.DataFrame(dict(key=g.key[mg], a=np.array(g.names)[g.i[mg]], b=np.array(g.names)[g.j[mg]], y=g.y[mg]))
    m = hh.merge(gg, on="key", suffixes=("_h", "_g"))
    # put both in a canonical orientation (alphabetical first model = 'first')
    def canon(y, a, b):
        return np.where(a > b, np.where(y == 1, 1, 2 - y), y)
    m["yh"] = canon(m.y_h.values, m.a_h.values, m.b_h.values)
    m["yg"] = canon(m.y_g.values, m.a_g.values, m.b_g.values)
    agree.append(dict(pair="mt_human_vs_gpt4", n=len(m), agree_all=float((m.yh == m.yg).mean()),
                      agree_nontie=float((m.yh == m.yg)[(m.yh != 1) & (m.yg != 1)].mean())))
    return pd.concat(rows), pd.DataFrame(sc), pd.DataFrame(agree)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--human-draws", type=int, default=20)
    ap.add_argument("--B", type=int, default=1000)
    a = ap.parse_args()
    b1, s1, a1 = mt_matched(a.human_draws, a.B)
    b1.to_csv(os.path.join(OUT, "s2_matched_budgets.csv"), index=False, float_format="%.6g")
    s1.to_csv(os.path.join(OUT, "s2_matched_scores.csv"), index=False, float_format="%.6g")
    a1.to_csv(os.path.join(OUT, "s2_matched_agreement.csv"), index=False, float_format="%.6g")
    prov.write_meta(os.path.join(OUT, "s2_matched.meta.json"), script="code/s2_matched.py", args=vars(a)
                    )


if __name__ == "__main__":
    main()
