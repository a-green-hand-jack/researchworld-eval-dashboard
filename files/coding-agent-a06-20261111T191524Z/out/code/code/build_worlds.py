"""Assemble outcome matrices (config x question) from cached letter-logits. Usage: python build_worlds.py [N_QUESTIONS=750]"""
import sys, numpy as np
sys.path.insert(0, "/work/code")
from worlds import load_real
nq = int(sys.argv[1]) if len(sys.argv) > 1 else 750
spec = dict(q15=("/work/results/q15", "/work/models/Qwen2.5-1.5B-Instruct", 'A'),
            b05=("/work/results/b05", "/work/models/Qwen2.5-0.5B-Instruct", 'B'),
            b15=("/work/results/b15", "/work/models/Qwen2.5-1.5B-Instruct", 'B'),
            s17=("/work/results/s17", "/work/models/SmolLM2-1.7B-Instruct", 'B'))
NQ = dict(q15=nq, b05=nq, b15=nq, s17=450)   # SmolLM2 world uses the first 450 pool questions
for w, (d, m, kind) in spec.items():
    try: Y, pool = load_real(d, 1500, 150, m, kind)
    except ValueError: print(w, 'no complete chunk yet'); continue
    if Y.shape[1] < NQ[w]: print(w, "incomplete:", Y.shape); continue
    Y = Y[:, :NQ[w]]; np.save(f"/work/results/world_{w}.npy", Y)
    print(w, Y.shape, "mean acc %.3f  sd of config acc %.4f  range %.3f-%.3f" % (Y.mean(), Y.mean(1).std(), Y.mean(1).min(), Y.mean(1).max()))
    if w == 'q15': pool.iloc[:nq][['question_id', 'category']].to_csv("/work/results/pool_ids.csv", index=False)
