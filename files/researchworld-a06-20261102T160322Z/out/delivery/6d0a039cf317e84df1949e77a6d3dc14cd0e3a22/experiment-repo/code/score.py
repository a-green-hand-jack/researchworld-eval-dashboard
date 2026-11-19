"""Score MMLU-Pro pool items under base prompt configs with llama.cpp (GGUF Q8_0); caches 10-way option log-probs.
usage: score.py MODEL N_POOL CHUNK WORKER NWORKERS [MAXCHUNKS]   (MODEL: qwen2.5-1.5b-instruct-q8_0 ...)
Tasks ordered (chunk, config); worker w takes tasks i with i % NWORKERS == w. Resumable."""
import sys, os, time, numpy as np
from llama_cpp import Llama
sys.path.insert(0, os.path.dirname(__file__))
import configs as C
model, n_pool, chunk, w, nw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
maxchunks = int(sys.argv[6]) if len(sys.argv) > 6 else 10**9
out = f"/hutian/repo/results/logits/{model}"; os.makedirs(out, exist_ok=True)
llm = Llama(model_path=f"/hutian/models/gguf/{model}.gguf", n_ctx=3072, n_threads=2, n_batch=512, verbose=False, seed=0)
test, val = C.load_test(), C.load_val()
pool = C.pool_indices(n_pool)
tk = lambda s: llm.tokenize(s.encode(), add_bos=False, special=True)
lid = [tk(c)[0] for c in C.LET]
nch = min((n_pool + chunk - 1) // chunk, maxchunks)
tasks = [(c, k) for c in range(nch) for k in range(len(C.BASE))]
def last_logits():
    return np.array(np.ctypeslib.as_array(llm._ctx.get_logits(), shape=(llm._n_vocab,)), dtype=np.float32)
def run(cidx, name, fn):
    rows = [test.iloc[i] for i in pool[cidx * chunk:(cidx + 1) * chunk]]
    order = sorted(range(len(rows)), key=lambda i: rows[i].category)
    res = np.full((len(rows), 10), -30.0, dtype=np.float32); cur = None; L0 = 0
    for i in order:
        r = rows[i]; pre, suf = C.prefix_suffix(name, r, val, r.category)
        if pre != cur:
            llm.reset(); p = tk(pre); llm.eval(p); L0 = len(p); cur = pre
        llm.n_tokens = L0
        s = tk(suf)[:1500]
        llm.eval(s)
        lg = last_logits()[lid][:len(r.options)]
        lg = lg - lg.max(); res[i, :len(r.options)] = lg - np.log(np.exp(lg).sum())
    np.save(fn, res.astype(np.float16))
for t, (c, k) in enumerate(tasks):
    if t % nw != w: continue
    name = C.BASE[k]; fn = f"{out}/{k:02d}__c{c}.npy"
    if os.path.exists(fn): continue
    t0 = time.time(); run(c, name, fn)
    print(f"HUTIAN_PROGRESS {model} cfg{k:02d} chunk{c} {time.time()-t0:.0f}s", flush=True)
