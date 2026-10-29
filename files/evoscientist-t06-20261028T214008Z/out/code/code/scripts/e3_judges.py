"""E3: same comparisons, different judges.

(a) MT-Bench: one expert vote per (question, model pair, turn) item vs. the GPT-4 pairwise
    judgment of the identical item.
(b) Chatbot Arena battles (potsawee/chatbot-arena-llm-judges): crowd label vs. each of 17
    open LLM judges on the identical set of battles.
-> results/e3_pairs.csv, results/e3_summary.csv
"""
from common import *  # noqa
import multiprocessing as mp
import numpy as np
import pandas as pd
from lbrobust import data as D
from lbrobust.analysis import analyze_dataset


def job(spec):
    kind, arg = spec
    if kind == "mt":
        dh, dj = D.mtbench_matched()
        agree = None
        group = "MT-Bench(matched)"
    else:
        df = D.llmjudge_pair(arg, return_df=True)
        dh, dj = D.llmjudge_pair(arg)
        agree = float((df.y_human == df.y_judge).mean())
        group = "Arena-LLMjudge"
    outs = []
    for d, src in ((dh, "human"), (dj, "judge")):
        pairs, s = analyze_dataset(d)
        s.update(group=group, judge=arg, label_source=src, label_agreement=agree,
                 tie_rate=float((d.n * (d.y == 0.5)).sum() / d.N))
        pairs["group"] = group
        pairs["judge"] = arg
        pairs["label_source"] = src
        outs.append((pairs, s))
    print(spec, flush=True)
    return outs


if __name__ == "__main__":
    specs = [("mt", "gpt4")] + [("arena", j) for j in D.JUDGES]
    D._battles()  # build cache once
    with Timer("e3"):
        with mp.Pool(NPROC) as p:
            out = p.map(job, specs, chunksize=1)
    pd.concat([o[0] for oo in out for o in oo]).to_csv(f"{RES}/e3_pairs.csv", index=False)
    pd.DataFrame([o[1] for oo in out for o in oo]).to_csv(f"{RES}/e3_summary.csv", index=False)
