"""Demonstration self-leakage: accuracy on items that appear as few-shot demos in the prompt vs. other items (Qwen2.5-1.5B, same prompt format as the grid).
Bootstrapped-demo optimisers (e.g. DSPy BootstrapFewShot) draw demos from the tuning set, so those items are scored with their own answer in the prompt.
Usage: python exp_leak.py OUT.npz [M_SETS] [N_OUT]"""
import sys, numpy as np, time
sys.path.insert(0, "/work/code")
from common import *
from scorer import Scorer
import grid
out = sys.argv[1]; M = int(sys.argv[2]) if len(sys.argv) > 2 else 40; NO = int(sys.argv[3]) if len(sys.argv) > 3 else 12
df = load_test(); pop = population_ids(1500, seed=0)
rng = np.random.default_rng(77)
sc = Scorer("/work/models/qwen2.5-1.5b-instruct-q8_0.gguf", n_threads=1)
f = 1; ins, cue = 0, 1          # "(A) text" format, instruction 0, cue "The answer is ("
res = []
def score_item(sc, P, r):
    body, _ = fmt_question(r, f)
    sc.llm._ctx.kv_cache_seq_rm(0, P, -1); sc.llm.n_tokens = P
    sc.llm.eval(sc.tok(body))
    Q = sc.llm.n_tokens
    st = sc.tok("\n" + grid.INSTR[ins] + "<|im_end|>\n<|im_start|>assistant\n" + grid.CUES[cue], special=True)
    sc.llm.eval(st)
    lg = np.array(np.ctypeslib.as_array(sc.llm._ctx.get_logits(), shape=(sc.llm._n_vocab,)), dtype=np.float64)
    nopt = len(r["options"])
    lp = np.array([np.logaddexp.reduce(lg[sc.letter_ids[o]]) for o in range(nopt)])
    return int(np.argmax(lp) == r["answer_index"])
for m in range(M):
    t = time.time()
    ids = rng.choice(len(pop), size=3 + NO, replace=False)
    demo_ids, out_ids = ids[:3], ids[3:]
    txt = ""
    for j in demo_ids:
        r = df.iloc[int(pop[j])]; body, _ = fmt_question(r, f)
        txt += body + "Answer: " + LETTERS[int(r["answer_index"])] + "\n\n"
    sc.set_prefix(txt); P = len(sc.prefix_toks)
    a_in = [score_item(sc, P, df.iloc[int(pop[j])]) for j in demo_ids]
    a_out = [score_item(sc, P, df.iloc[int(pop[j])]) for j in out_ids]
    # control: the same demo items scored under a prompt whose demos are a *different* random set (no self-answer in prompt)
    res.append((np.mean(a_in), np.mean(a_out), a_in, a_out))
    print(m, np.mean(a_in), np.mean(a_out), f"{time.time()-t:.0f}s", flush=True)
    np.savez(out, a_in=np.array([r[2] for r in res]), a_out=np.array([r[3] for r in res]))
