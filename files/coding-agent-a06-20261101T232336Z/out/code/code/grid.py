"""Compute the full (config x item) log-prob cache on a fixed population of MMLU-Pro items.
Config = (group g = (option format, demo set) in the shared prefix) x (suffix s = (instruction, answer cue)).
Usage: python grid.py MODEL_GGUF OUTDIR WORKER NWORKERS [N_POP] [CHUNK]"""
import sys, os, time, numpy as np
sys.path.insert(0, "/work/code")
from common import *
from scorer import Scorer

FMT_G = [0, 1]                 # option label styles: "A. x", "(A) x"
DEMO_G = [0, 1, 2]             # 0: zero-shot, 1,2: two different 3-shot demo sets from the validation split
GROUPS = [(f, d) for f in FMT_G for d in DEMO_G]
INSTR = ["Choose the correct answer.",
         "Respond with only the letter of the correct option.",
         "Think step by step about each option, then give the single best answer.",
         "You are an expert. Select the most accurate option."]
CUES = ["Answer:", "The answer is (", "Correct option:"]
SUFFIXES = [(i, c) for i in range(len(INSTR)) for c in range(len(CUES))]
G, S = len(GROUPS), len(SUFFIXES)

def demo_text(val, ds, d, f):
    s = ""
    for j in ds[d]:
        r = val.iloc[int(j)]
        body, _ = fmt_question(r, f)
        s += body + "Answer: " + LETTERS[int(r["answer_index"])] + "\n\n"
    return s

if __name__ == "__main__":
    model, outdir, w, W = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    N = int(sys.argv[5]) if len(sys.argv) > 5 else 1000
    CH = int(sys.argv[6]) if len(sys.argv) > 6 else 25
    os.makedirs(outdir, exist_ok=True)
    df = load_test(); val = load_val(); ds = demo_sets(val)
    pop = population_ids(N, seed=0)
    perm = np.random.default_rng(1).permutation(N)           # processing order (random => any prefix of chunks is a random subsample)
    sc = Scorer(model, n_threads=1, n_ctx=4096)
    nch = (N + CH - 1) // CH
    rev = len(sys.argv) > 7 and sys.argv[7] == 'rev'
    kk = list(range(47, -1, -1)) if rev else list(range(w, nch, W))
    for k in kk:
        fn = f"{outdir}/chunk_{k:04d}.npz"
        if os.path.exists(fn): continue
        t0 = time.time()
        items = perm[k * CH:(k + 1) * CH]
        rows = [df.iloc[int(pop[i])] for i in items]
        out = np.full((len(items), G * S, 10), -np.inf, dtype=np.float32)
        for gi, (f, d) in enumerate(GROUPS):
            sc.set_prefix(demo_text(val, ds, d, f))
            P = len(sc.prefix_toks)
            for ii, r in enumerate(rows):
                body, _ = fmt_question(r, f)
                nopt = len(r["options"])
                qtoks = sc.tok(body, special=False)
                sc.llm._ctx.kv_cache_seq_rm(0, P, -1); sc.llm.n_tokens = P
                sc.llm.eval(qtoks)
                Q = sc.llm.n_tokens
                for si, (ins, cue) in enumerate(SUFFIXES):
                    stoks = sc.tok("\n" + INSTR[ins] + "<|im_end|>\n<|im_start|>assistant\n" + CUES[cue], special=True)
                    sc.llm._ctx.kv_cache_seq_rm(0, Q, -1); sc.llm.n_tokens = Q
                    sc.llm.eval(stoks)
                    lg = np.array(np.ctypeslib.as_array(sc.llm._ctx.get_logits(), shape=(sc.llm._n_vocab,)), dtype=np.float64)
                    lg -= np.logaddexp.reduce(lg)
                    out[ii, gi * S + si, :nopt] = [np.logaddexp.reduce(lg[sc.letter_ids[o]]) for o in range(nopt)]
        np.savez(fn + ".tmp.npz", lp=out, item_pos=pop[items], item_perm=items)
        os.rename(fn + ".tmp.npz", fn)
        print(f"worker {w} chunk {k}/{nch} done in {time.time()-t0:.0f}s", flush=True)
