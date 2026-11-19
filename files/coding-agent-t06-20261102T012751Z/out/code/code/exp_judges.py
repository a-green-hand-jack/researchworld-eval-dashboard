"""Same-battle comparison: the 49,938 single-turn Arena battles labelled by humans vs three LLM
judges, plus a human variant with ties dropped (to match the near-tie-free judge labels), and
tie-dropped variants of MT-Bench human.  All pairs, same protocol as exp_main.
Writes results/pairs_judges.csv"""
import time, numpy as np, pandas as pd
from multiprocessing import Pool
import exp_main as M
import datasets as ds

def drop_ties(b, name):
    N = b.N.copy(); N[:, 1] = 0
    out = b.with_counts(N); out.name = name
    return out

if __name__ == "__main__":
    B = M.BOARDS
    h = ds.arena_single_turn()
    B["st_human"] = h
    B["st_human_noties"] = drop_ties(h, "st human, ties dropped")
    for key, j in [("st_athene70b", "Athene-70B"), ("st_mistral7b", "Mistral-7B-Instruct-v0.2"), ("st_llama3_8b", "Meta-Llama-3-8B-Instruct")]:
        B[key] = ds.arena_single_turn(j)
    B["mt_human_noties"] = drop_ties(ds.mtbench_human(), "mt human no ties")
    tasks = []
    for key, b in B.items():
        s = b.fit()[: b.m]
        tasks += [(key, i, j) for i in range(b.m) for j in range(b.m) if s[i] > s[j]]
    tasks.sort(key=lambda t: -B[t[0]].n)
    t0 = time.time(); print(len(tasks), flush=True)
    with Pool(38) as p:
        out = sum(p.imap_unordered(M.task, tasks, chunksize=4), [])
    pd.DataFrame(out).to_csv("/work/results/pairs_judges.csv", index=False)
    print("done", time.time() - t0)
