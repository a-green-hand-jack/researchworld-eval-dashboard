"""Real-II pool: model x prompt.  For ONE model, compute per-item letter log-probs for 2 groups (zero-shot, 3-shot) x 4 suffixes
(instruction in {0,1} x cue in {0,1}) on the first NCH chunks of the same item permutation as grid.py.
Usage: python grid2.py MODEL_GGUF OUTDIR TEMPLATE(chatml|qwen3) [NCH]"""
import sys, os, time, numpy as np
sys.path.insert(0, "/work/code")
from common import *
from scorer import Scorer
import grid

model, outdir, tmpl = sys.argv[1], sys.argv[2], sys.argv[3]
NCH = int(sys.argv[4]) if len(sys.argv) > 4 else 24
N, CH = 1500, 25
GROUPS = [(0, 0), (0, 1)]                  # (format 0 "A. text"), demo sets 0 (zero-shot) and 1 (3-shot)
SUF = [(i, c) for i in (0, 1) for c in (0, 1)]
ASSIST = "<|im_start|>assistant\n" + ("<think>\n\n</think>\n\n" if tmpl == "qwen3" else "")
os.makedirs(outdir, exist_ok=True)
df = load_test(); val = load_val(); ds = demo_sets(val)
pop = population_ids(N, seed=0); perm = np.random.default_rng(1).permutation(N)
sc = Scorer(model, n_threads=1, n_ctx=4096)
for k in range(NCH):
    fn = f"{outdir}/chunk_{k:04d}.npz"
    if os.path.exists(fn): continue
    t0 = time.time(); items = perm[k * CH:(k + 1) * CH]; rows = [df.iloc[int(pop[i])] for i in items]
    out = np.full((len(items), len(GROUPS) * len(SUF), 10), -np.inf, dtype=np.float32)
    for gi, (f, d) in enumerate(GROUPS):
        sc.set_prefix(grid.demo_text(val, ds, d, f)); P = len(sc.prefix_toks)
        for ii, r in enumerate(rows):
            body, _ = fmt_question(r, f); nopt = len(r["options"])
            sc.llm._ctx.kv_cache_seq_rm(0, P, -1); sc.llm.n_tokens = P
            sc.llm.eval(sc.tok(body)); Q = sc.llm.n_tokens
            for si, (ins, cue) in enumerate(SUF):
                st = sc.tok("\n" + grid.INSTR[ins] + "<|im_end|>\n" + ASSIST + grid.CUES[cue], special=True)
                sc.llm._ctx.kv_cache_seq_rm(0, Q, -1); sc.llm.n_tokens = Q; sc.llm.eval(st)
                lg = np.array(np.ctypeslib.as_array(sc.llm._ctx.get_logits(), shape=(sc.llm._n_vocab,)), dtype=np.float64); lg -= np.logaddexp.reduce(lg)
                out[ii, gi * len(SUF) + si, :nopt] = [np.logaddexp.reduce(lg[sc.letter_ids[o]]) for o in range(nopt)]
    np.savez(fn + ".tmp.npz", lp=out, item_pos=pop[items], item_perm=items); os.rename(fn + ".tmp.npz", fn)
    print(f"chunk {k} {time.time()-t0:.0f}s", flush=True)
